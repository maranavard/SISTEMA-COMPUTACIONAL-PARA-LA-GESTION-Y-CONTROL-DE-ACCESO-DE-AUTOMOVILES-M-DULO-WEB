from __future__ import annotations

import math
from datetime import datetime

import numpy as np
import pandas as pd
from sqlalchemy import create_engine

DB_URL = "postgresql+psycopg2://postgres:12345@localhost:5432/sistema_control"
CSV_OUT = "ocupacion_5min.csv"
FREQ = "5min"

# Cantidad mínima de muestras para entrenar LSTM con estabilidad para demo.
MIN_SAMPLES_FOR_TRAIN = 1000
# Generación ficticia por defecto: 90 días -> 25.920 muestras de 5 min.
DEFAULT_SYNTH_DAYS = 90


def _try_load_real_events() -> pd.DataFrame:
    engine = create_engine(DB_URL)

    queries = [
        """
        SELECT
            n.id,
            n.id_vehiculo,
            n.fecha_hora AS timestamp,
            lower(n.tipo_novedad) AS concepto,
            CASE
                WHEN n.id_vehiculo IS NOT NULL THEN 1
                ELSE 0
            END AS registrado
        FROM public.novedad n
        WHERE n.fecha_hora IS NOT NULL
          AND lower(n.tipo_novedad) IN ('ingreso', 'entrada', 'salida')
        ORDER BY n.fecha_hora ASC
        """,
        """
        SELECT
            rv.id,
            rv.id_vehiculo,
            rv.fecha_registro AS timestamp,
            lower(rv.concepto) AS concepto,
            CASE
                WHEN rv.id_vehiculo IS NOT NULL THEN 1
                ELSE 0
            END AS registrado
        FROM registro_visitantes rv
        WHERE rv.fecha_registro IS NOT NULL
        ORDER BY rv.fecha_registro ASC
        """,
    ]

    last_error: Exception | None = None
    for query in queries:
        try:
            df = pd.read_sql(query, engine)
            if len(df) > 0:
                return df
        except Exception as exc:
            last_error = exc

    if last_error is not None:
        print(f"[ETL] Sin datos reales utilizables: {last_error}")
    return pd.DataFrame(columns=["id", "id_vehiculo", "timestamp", "concepto", "registrado"])


def _simulate_occupancy_series(days: int = DEFAULT_SYNTH_DAYS, capacity: int = 50) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    periods = int((days * 24 * 60) / 5)
    end = pd.Timestamp(datetime.now()).floor(FREQ)
    idx = pd.date_range(end=end, periods=periods, freq=FREQ)

    ocupados = []
    porcentaje_registrados = []
    current = 0

    for ts in idx:
        hour = ts.hour
        weekday = ts.dayofweek

        morning_peak = math.exp(-((hour - 8.0) ** 2) / 6.0)
        afternoon_peak = math.exp(-((hour - 13.5) ** 2) / 8.0)
        weekday_factor = 1.0 if weekday < 5 else 0.55
        intensity = weekday_factor * (0.20 + 0.55 * morning_peak + 0.45 * afternoon_peak)

        trend_target = int(np.clip(round(capacity * intensity + rng.normal(0, 2.2)), 0, capacity))
        delta = int(np.clip(round((trend_target - current) * 0.20 + rng.normal(0, 1.2)), -4, 4))
        current = int(np.clip(current + delta, 0, capacity))

        reg_ratio = float(np.clip(0.80 + 0.12 * weekday_factor + rng.normal(0, 0.04), 0.60, 0.98))

        ocupados.append(current)
        porcentaje_registrados.append(reg_ratio)

    df = pd.DataFrame(
        {
            "timestamp": idx,
            "ocupados": ocupados,
            "registrado_ratio": porcentaje_registrados,
        }
    )
    return df


def _events_to_occupancy(df_events: pd.DataFrame, capacity: int = 50) -> pd.DataFrame:
    df = df_events.copy()
    if len(df) == 0:
        return pd.DataFrame(columns=["timestamp", "ocupados", "registrado_ratio"])

    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df.dropna(subset=["timestamp"])
    if len(df) == 0:
        return pd.DataFrame(columns=["timestamp", "ocupados", "registrado_ratio"])

    df["concepto"] = (df["concepto"].astype(str).str.strip().str.lower())
    df["registrado"] = pd.to_numeric(df.get("registrado", 1), errors="coerce").fillna(1).clip(0, 1)
    df = df[df["concepto"].isin(["ingreso", "entrada", "salida"])]
    if len(df) == 0:
        return pd.DataFrame(columns=["timestamp", "ocupados", "registrado_ratio"])

    df["bucket"] = df["timestamp"].dt.floor(FREQ)
    grouped = df.groupby("bucket", as_index=False).agg(
        ingresos=("concepto", lambda values: int(((values == "ingreso") | (values == "entrada")).sum())),
        salidas=("concepto", lambda values: int((values == "salida").sum())),
        registrado_ratio=("registrado", "mean"),
    )

    idx = pd.date_range(grouped["bucket"].min(), grouped["bucket"].max(), freq=FREQ)
    serie = pd.DataFrame({"timestamp": idx}).merge(grouped, left_on="timestamp", right_on="bucket", how="left")
    serie = serie.drop(columns=["bucket"])
    serie[["ingresos", "salidas"]] = serie[["ingresos", "salidas"]].fillna(0)
    serie["registrado_ratio"] = serie["registrado_ratio"].fillna(method="ffill").fillna(0.9)

    current = 0
    ocupados = []
    for row in serie.itertuples(index=False):
        current = max(0, min(capacity, current + int(row.ingresos) - int(row.salidas)))
        ocupados.append(current)

    serie["ocupados"] = ocupados
    return serie[["timestamp", "ocupados", "registrado_ratio"]]


def build_dataset() -> pd.DataFrame:
    real_events = _try_load_real_events()
    real_series = _events_to_occupancy(real_events)

    if len(real_series) >= MIN_SAMPLES_FOR_TRAIN:
        print(f"[ETL] Usando datos reales: {len(real_series)} muestras.")
        return real_series

    synth = _simulate_occupancy_series(days=DEFAULT_SYNTH_DAYS, capacity=50)
    if len(real_series) > 0:
        merged = pd.concat([real_series, synth], ignore_index=True)
        merged = merged.sort_values("timestamp").drop_duplicates(subset=["timestamp"], keep="last")
        print(
            f"[ETL] Datos reales insuficientes ({len(real_series)}). "
            f"Completado con sintéticos -> {len(merged)} muestras."
        )
        return merged

    print(f"[ETL] Sin historial usable. Generados datos sintéticos: {len(synth)} muestras.")
    return synth


def main() -> None:
    df = build_dataset()
    if len(df) == 0:
        raise RuntimeError("No se pudieron generar datos para entrenamiento LSTM.")

    df = df.sort_values("timestamp").reset_index(drop=True)
    df["hora"] = df["timestamp"].dt.hour
    df["dia_semana"] = df["timestamp"].dt.dayofweek

    df.to_csv(CSV_OUT, index=False)
    print(f"[ETL] Archivo generado: {CSV_OUT}")
    print(f"[ETL] Rango: {df['timestamp'].min()} -> {df['timestamp'].max()}")
    print(f"[ETL] Muestras: {len(df)}")


if __name__ == "__main__":
    main()

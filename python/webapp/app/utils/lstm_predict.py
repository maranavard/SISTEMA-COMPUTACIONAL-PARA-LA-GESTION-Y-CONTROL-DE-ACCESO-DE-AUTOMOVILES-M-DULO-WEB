"""Utilidades para integración de ETL + LSTM desde la aplicación web."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def _python_root() -> Path:
    # Compatibilidad: se mantiene para componentes que aún usen rutas antiguas.
    return Path(__file__).resolve().parents[3]


def _repo_root() -> Path:
    # .../python/webapp/app/utils/lstm_predict.py -> .../<repo>
    return Path(__file__).resolve().parents[4]


def _ia_root() -> Path:
    return _repo_root() / "ia"


def _ensure_prediction_dependencies():
    try:
        import joblib
        import numpy as np
        import pandas as pd
        return joblib, np, pd
    except Exception as exc:
        raise RuntimeError(
            "Faltan dependencias para predicción LSTM (joblib, numpy, pandas)."
        ) from exc


def _ensure_prediction_inputs(
    csv_path: Path,
    model_path: Path,
    fallback_model_path: Path,
    scaler_x_path: Path,
    scaler_path: Path,
) -> None:
    if not csv_path.exists():
        raise FileNotFoundError("No existe ocupacion_5min.csv. Ejecuta ETL primero.")
    if (not model_path.exists() and not fallback_model_path.exists()) or not scaler_path.exists() or not scaler_x_path.exists():
        raise FileNotFoundError("No existe modelo/scalers de predicción. Ejecuta entrenamiento primero.")


def _build_features_dataframe(df, pd):
    if "ocupados" not in df.columns:
        raise ValueError("El CSV de ocupación no contiene la columna 'ocupados'.")
    if "hora" not in df.columns:
        df["hora"] = pd.to_datetime(df["timestamp"]).dt.hour if "timestamp" in df.columns else 0
    if "dia_semana" not in df.columns:
        df["dia_semana"] = pd.to_datetime(df["timestamp"]).dt.dayofweek if "timestamp" in df.columns else 0
    if "registrado_ratio" not in df.columns:
        df["registrado_ratio"] = 0.9
    return df[["ocupados", "hora", "dia_semana", "registrado_ratio"]].astype("float32")


def _predict_scaled(window_scaled, model_path: Path, fallback_model_path: Path, joblib):
    pred_scaled = None
    if model_path.exists():
        try:
            from tensorflow.keras.models import load_model

            model = load_model(model_path)
            pred_scaled = model.predict(window_scaled, verbose=0)[0]
        except Exception:
            pred_scaled = None

    if pred_scaled is None:
        if not fallback_model_path.exists():
            raise RuntimeError("No se pudo cargar LSTM y no existe modelo de respaldo.")
        fallback_model = joblib.load(fallback_model_path)
        pred_scaled = fallback_model.predict(window_scaled.reshape(1, -1))[0]

    return pred_scaled


def train_lstm_pipeline(timeout_seconds: int = 240) -> dict:
    ia_root = _ia_root()
    etl_path = ia_root / "etl.py"
    train_path = ia_root / "train_lstm.py"

    if not etl_path.exists() or not train_path.exists():
        raise FileNotFoundError("No se encontró etl.py o train_lstm.py en el proyecto.")

    etl_result = subprocess.run(
        [sys.executable, str(etl_path)],
        cwd=str(ia_root),
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
        check=False,
    )
    if etl_result.returncode != 0:
        raise RuntimeError((etl_result.stderr or etl_result.stdout or "Error ETL").strip())

    train_result = subprocess.run(
        [sys.executable, str(train_path)],
        cwd=str(ia_root),
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
        check=False,
    )
    if train_result.returncode != 0:
        raise RuntimeError((train_result.stderr or train_result.stdout or "Error entrenamiento LSTM").strip())

    return {
        "etl": (etl_result.stdout or "").strip(),
        "train": (train_result.stdout or "").strip(),
    }


def predict_next_40_minutes() -> dict:
    joblib, np, pd = _ensure_prediction_dependencies()

    ia_root = _ia_root()
    csv_path = ia_root / "ocupacion_5min.csv"
    model_path = ia_root / "lstm_model_v1.h5"
    fallback_model_path = ia_root / "lstm_model_fallback.pkl"
    scaler_x_path = ia_root / "scaler_x_v1.pkl"
    scaler_path = ia_root / "scaler_y_v1.pkl"

    _ensure_prediction_inputs(
        csv_path=csv_path,
        model_path=model_path,
        fallback_model_path=fallback_model_path,
        scaler_x_path=scaler_x_path,
        scaler_path=scaler_path,
    )

    df = pd.read_csv(csv_path)
    features = _build_features_dataframe(df, pd)
    series = df["ocupados"].astype("float32").to_numpy()
    t_past = 24
    if len(series) < t_past:
        raise ValueError("No hay suficientes datos para predecir (mínimo 24 muestras).")

    scaler_x = joblib.load(scaler_x_path)
    scaler = joblib.load(scaler_path)

    window_features = features.tail(t_past)
    window_array = window_features.to_numpy()
    window_scaled = scaler_x.transform(window_features).reshape((1, t_past, window_array.shape[1]))

    pred_scaled = _predict_scaled(
        window_scaled=window_scaled,
        model_path=model_path,
        fallback_model_path=fallback_model_path,
        joblib=joblib,
    )

    pred = scaler.inverse_transform(pred_scaled.reshape(-1, 1)).reshape(-1)
    pred = np.clip(pred, 0, None)

    pred_list = [int(round(value)) for value in pred.tolist()]
    return {
        "horizonte_min": 40,
        "pasos": len(pred_list),
        "serie": pred_list,
        "promedio": int(round(float(np.mean(pred)))),
        "maximo": int(round(float(np.max(pred)))),
    }

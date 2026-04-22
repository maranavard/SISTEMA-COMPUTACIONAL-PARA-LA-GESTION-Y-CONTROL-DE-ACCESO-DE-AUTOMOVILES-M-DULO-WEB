"""Configuración de horarios operativos y festivos del sistema."""

from __future__ import annotations

from datetime import date, datetime

from app.db import get_connection


class HorarioOperacion:
    DEFAULT_HORA_INICIO = "06:00"
    DEFAULT_HORA_FIN = "22:00"
    # Monday=0 ... Sunday=6
    DEFAULT_DIAS_ACTIVOS = "0,1,2,3,4,5"

    @classmethod
    def _ensure_tables(cls) -> None:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS public.config_horario_universidad (
                        id SMALLINT PRIMARY KEY,
                        hora_inicio TIME NOT NULL,
                        hora_fin TIME NOT NULL,
                        dias_activos VARCHAR(40) NOT NULL,
                        updated_at TIMESTAMP NOT NULL DEFAULT NOW()
                    )
                    """
                )
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS public.config_festivos_universidad (
                        fecha DATE PRIMARY KEY,
                        descripcion VARCHAR(120),
                        updated_at TIMESTAMP NOT NULL DEFAULT NOW()
                    )
                    """
                )
                cur.execute(
                    """
                    INSERT INTO public.config_horario_universidad (id, hora_inicio, hora_fin, dias_activos)
                    VALUES (1, %s::time, %s::time, %s)
                    ON CONFLICT (id) DO NOTHING
                    """,
                    (cls.DEFAULT_HORA_INICIO, cls.DEFAULT_HORA_FIN, cls.DEFAULT_DIAS_ACTIVOS),
                )
            conn.commit()

    @staticmethod
    def _parse_dias_activos(raw: str) -> list[int]:
        values: list[int] = []
        for part in (raw or "").split(","):
            item = part.strip()
            if not item:
                continue
            try:
                day = int(item)
            except ValueError:
                continue
            if 0 <= day <= 6 and day not in values:
                values.append(day)
        return sorted(values)

    @classmethod
    def get_config(cls) -> dict:
        cls._ensure_tables()

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT hora_inicio::text, hora_fin::text, dias_activos
                    FROM public.config_horario_universidad
                    WHERE id = 1
                    LIMIT 1
                    """
                )
                row = cur.fetchone()

                cur.execute(
                    """
                    SELECT fecha, COALESCE(descripcion, '')
                    FROM public.config_festivos_universidad
                    ORDER BY fecha ASC
                    """
                )
                festivos_rows = cur.fetchall()

        if not row:
            return {
                "hora_inicio": cls.DEFAULT_HORA_INICIO,
                "hora_fin": cls.DEFAULT_HORA_FIN,
                "dias_activos": cls._parse_dias_activos(cls.DEFAULT_DIAS_ACTIVOS),
                "festivos": [],
            }

        festivos = []
        for fecha, descripcion in festivos_rows:
            festivos.append({"fecha": fecha, "descripcion": descripcion or ""})

        return {
            "hora_inicio": str(row[0])[:5],
            "hora_fin": str(row[1])[:5],
            "dias_activos": cls._parse_dias_activos(row[2]),
            "festivos": festivos,
        }

    @classmethod
    def update_config(
        cls,
        hora_inicio: str,
        hora_fin: str,
        dias_activos: list[int],
        festivos_texto: str,
    ) -> None:
        cls._ensure_tables()

        normalized_days = sorted({day for day in dias_activos if 0 <= day <= 6})
        if not normalized_days:
            raise ValueError("Debes seleccionar al menos un día activo.")

        days_text = ",".join(str(day) for day in normalized_days)

        parsed_festivos: list[tuple[date, str]] = []
        seen_dates: set[date] = set()
        for raw_line in (festivos_texto or "").splitlines():
            line = raw_line.strip()
            if not line:
                continue

            if "|" in line:
                date_part, desc_part = line.split("|", 1)
            elif ";" in line:
                date_part, desc_part = line.split(";", 1)
            else:
                date_part, desc_part = line, ""

            date_text = date_part.strip()
            desc_text = desc_part.strip()

            try:
                parsed_date = datetime.strptime(date_text, "%Y-%m-%d").date()
            except ValueError as exc:
                raise ValueError(f"Fecha festiva inválida: {date_text}. Usa formato AAAA-MM-DD.") from exc

            if parsed_date in seen_dates:
                continue

            seen_dates.add(parsed_date)
            parsed_festivos.append((parsed_date, desc_text[:120]))

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE public.config_horario_universidad
                    SET hora_inicio = %s::time,
                        hora_fin = %s::time,
                        dias_activos = %s,
                        updated_at = NOW()
                    WHERE id = 1
                    """,
                    (hora_inicio, hora_fin, days_text),
                )

                cur.execute("DELETE FROM public.config_festivos_universidad")
                for festivo_date, festivo_desc in parsed_festivos:
                    cur.execute(
                        """
                        INSERT INTO public.config_festivos_universidad (fecha, descripcion)
                        VALUES (%s, %s)
                        """,
                        (festivo_date, festivo_desc),
                    )
            conn.commit()

    @classmethod
    def evaluate_moment(cls, moment: datetime | None = None) -> dict:
        now = moment or datetime.now()
        config = cls.get_config()

        dias_activos = set(config.get("dias_activos") or [])
        hora_inicio = datetime.strptime(config.get("hora_inicio", cls.DEFAULT_HORA_INICIO), "%H:%M").time()
        hora_fin = datetime.strptime(config.get("hora_fin", cls.DEFAULT_HORA_FIN), "%H:%M").time()

        current_date = now.date()
        current_weekday = now.weekday()
        current_time = now.time()

        festivos_set = {item["fecha"] for item in config.get("festivos", [])}
        is_holiday = current_date in festivos_set
        is_active_day = current_weekday in dias_activos
        in_time_range = hora_inicio <= current_time < hora_fin

        reason = "operativo"
        if is_holiday:
            reason = "festivo"
        elif not is_active_day:
            reason = "dia_inactivo"
        elif not in_time_range:
            reason = "fuera_de_horario"

        return {
            "is_holiday": is_holiday,
            "is_sunday": current_weekday == 6,
            "is_active_day": is_active_day,
            "in_time_range": in_time_range,
            "is_operational": is_active_day and in_time_range and not is_holiday,
            "reason": reason,
            "now": now,
        }
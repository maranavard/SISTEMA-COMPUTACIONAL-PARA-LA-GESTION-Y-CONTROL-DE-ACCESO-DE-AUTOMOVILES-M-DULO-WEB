"""Gestión de documentos vehiculares y su vigencia."""

from __future__ import annotations

from datetime import date

from app.db import get_connection


class DocumentoVehiculo:
    REQUIRED_DOCS = {
        "soat": "SOAT",
        "tecnomecanica": "Técnico-mecánica",
        "tarjeta_propiedad": "Tarjeta de propiedad",
    }

    @classmethod
    def _ensure_tables(cls) -> None:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS public.tipo_documento (
                        id SERIAL PRIMARY KEY,
                        codigo VARCHAR(30) UNIQUE NOT NULL,
                        nombre VARCHAR(100) NOT NULL,
                        descripcion TEXT,
                        entidad_objetivo VARCHAR(30) NOT NULL DEFAULT 'vehiculo',
                        activo BOOLEAN NOT NULL DEFAULT TRUE,
                        created_at TIMESTAMP NOT NULL DEFAULT NOW()
                    )
                    """
                )

                cur.execute(
                    """
                    INSERT INTO public.tipo_documento (codigo, nombre, entidad_objetivo)
                    VALUES
                        ('soat', 'SOAT', 'vehiculo'),
                        ('tecnomecanica', 'Técnico-mecánica', 'vehiculo'),
                        ('tarjeta_propiedad', 'Tarjeta de propiedad', 'vehiculo')
                    ON CONFLICT (codigo) DO NOTHING
                    """
                )

                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS public.documentos_vehiculo (
                        id SERIAL PRIMARY KEY,
                        vehiculo_id INTEGER NOT NULL,
                        tipo_documento_id INTEGER NOT NULL REFERENCES public.tipo_documento(id),
                        archivo_url TEXT,
                        fecha_registro DATE NOT NULL DEFAULT CURRENT_DATE,
                        fecha_vencimiento DATE,
                        estado VARCHAR(20) NOT NULL DEFAULT 'vigente',
                        created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                        updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
                        UNIQUE (vehiculo_id, tipo_documento_id)
                    )
                    """
                )

                cur.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_doc_vehiculo_venc
                    ON public.documentos_vehiculo (fecha_vencimiento)
                    """
                )
            conn.commit()

    @classmethod
    def _get_doc_type_map(cls) -> dict[str, int]:
        cls._ensure_tables()
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, codigo
                    FROM public.tipo_documento
                    WHERE entidad_objetivo = 'vehiculo'
                    """
                )
                rows = cur.fetchall()

        return {str(row[1] or "").strip().lower(): int(row[0]) for row in rows}

    @classmethod
    def upsert_documents(cls, vehiculo_id: int, docs_expiration: dict[str, str]) -> None:
        cls._ensure_tables()
        doc_type_map = cls._get_doc_type_map()

        with get_connection() as conn:
            with conn.cursor() as cur:
                for code in cls.REQUIRED_DOCS.keys():
                    raw_date = (docs_expiration.get(code) or "").strip()
                    if not raw_date:
                        continue

                    tipo_id = doc_type_map.get(code)
                    if not tipo_id:
                        continue

                    cur.execute(
                        """
                        INSERT INTO public.documentos_vehiculo (
                            vehiculo_id,
                            tipo_documento_id,
                            fecha_registro,
                            fecha_vencimiento,
                            estado,
                            updated_at
                        )
                        VALUES (%s, %s, CURRENT_DATE, %s::date, 'vigente', NOW())
                        ON CONFLICT (vehiculo_id, tipo_documento_id)
                        DO UPDATE SET
                            fecha_vencimiento = EXCLUDED.fecha_vencimiento,
                            estado = 'vigente',
                            updated_at = NOW()
                        """,
                        (vehiculo_id, tipo_id, raw_date),
                    )
            conn.commit()

    @classmethod
    def get_vehicle_documents(cls, vehiculo_id: int) -> dict[str, dict]:
        cls._ensure_tables()

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        td.codigo,
                        td.nombre,
                        dv.fecha_vencimiento,
                        COALESCE(dv.estado, 'vigente')
                    FROM public.documentos_vehiculo dv
                    INNER JOIN public.tipo_documento td ON td.id = dv.tipo_documento_id
                    WHERE dv.vehiculo_id = %s
                      AND td.entidad_objetivo = 'vehiculo'
                    """,
                    (vehiculo_id,),
                )
                rows = cur.fetchall()

        result: dict[str, dict] = {}
        for row in rows:
            code = str(row[0] or "").strip().lower()
            result[code] = {
                "codigo": code,
                "nombre": row[1] or code,
                "fecha_vencimiento": row[2],
                "estado": (row[3] or "vigente").strip().lower(),
            }
        return result

    @classmethod
    def get_status_summary(cls, vehiculo_id: int, warning_days: int = 30) -> dict:
        docs = cls.get_vehicle_documents(vehiculo_id)
        today = date.today()

        warning_messages: list[str] = []
        for code, label in cls.REQUIRED_DOCS.items():
            doc = docs.get(code)
            if not doc:
                return {
                    "ok": False,
                    "level": "error",
                    "message": f"Falta registrar {label} del vehículo.",
                    "block_automatic_assignment": True,
                }

            fecha_vencimiento = doc.get("fecha_vencimiento")
            if not fecha_vencimiento:
                return {
                    "ok": False,
                    "level": "error",
                    "message": f"{label} no tiene fecha de vencimiento registrada.",
                    "block_automatic_assignment": True,
                }

            if hasattr(fecha_vencimiento, "date"):
                fecha_vencimiento = fecha_vencimiento.date()
            if not isinstance(fecha_vencimiento, date):
                return {
                    "ok": False,
                    "level": "error",
                    "message": f"No se pudo interpretar la fecha de vencimiento de {label}.",
                    "block_automatic_assignment": True,
                }

            days_to_expire = (fecha_vencimiento - today).days
            if days_to_expire < 0:
                return {
                    "ok": False,
                    "level": "error",
                    "message": f"{label} está vencido ({abs(days_to_expire)} días).",
                    "block_automatic_assignment": True,
                }
            if days_to_expire <= warning_days:
                warning_messages.append(f"{label} vence en {days_to_expire} días")

        if warning_messages:
            return {
                "ok": True,
                "level": "warning",
                "message": "; ".join(warning_messages) + ".",
                "block_automatic_assignment": False,
            }

        return {
            "ok": True,
            "level": "success",
            "message": "Documentación vehicular vigente.",
            "block_automatic_assignment": False,
        }

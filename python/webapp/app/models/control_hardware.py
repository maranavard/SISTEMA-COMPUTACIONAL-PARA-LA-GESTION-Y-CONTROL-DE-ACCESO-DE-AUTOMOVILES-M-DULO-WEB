"""Estado y control manual de dispositivos de acceso."""

from __future__ import annotations

from app.db import get_connection
from psycopg2.extras import Json


class ControlHardware:
    DEVICES = [
        {
            "clave": "talanquera_principal",
            "nombre": "Talanquera principal",
            "descripcion": "Permite apertura o cierre manual de la talanquera principal.",
        },
        {
            "clave": "semaforo_verde",
            "nombre": "Semaforo verde",
            "descripcion": "Activa o desactiva luz verde para autorizacion de paso.",
        },
        {
            "clave": "semaforo_rojo",
            "nombre": "Semaforo rojo",
            "descripcion": "Activa o desactiva luz roja para denegacion de paso.",
        },
    ]

    @classmethod
    def _ensure_table(cls) -> None:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS public.control_hardware_estado (
                        clave VARCHAR(80) PRIMARY KEY,
                        nombre VARCHAR(120) NOT NULL,
                        descripcion VARCHAR(240),
                        encendido BOOLEAN NOT NULL DEFAULT FALSE,
                        updated_by INTEGER,
                        updated_at TIMESTAMP NOT NULL DEFAULT NOW()
                    )
                    """
                )

                for item in cls.DEVICES:
                    cur.execute(
                        """
                        INSERT INTO public.control_hardware_estado (clave, nombre, descripcion, encendido)
                        VALUES (%s, %s, %s, FALSE)
                        ON CONFLICT (clave) DO NOTHING
                        """,
                        (item["clave"], item["nombre"], item["descripcion"]),
                    )

                # Limpia un dispositivo legado que ya no se usa en la UI.
                cur.execute(
                    "DELETE FROM public.control_hardware_estado WHERE clave = %s",
                    ("modo_manual_emergencia",),
                )
            conn.commit()

    @classmethod
    def _ensure_events_table(cls) -> None:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS public.control_hardware_eventos (
                        event_id VARCHAR(80) PRIMARY KEY,
                        event_type VARCHAR(60) NOT NULL,
                        source_device VARCHAR(120) NOT NULL,
                        occurred_at TIMESTAMP NOT NULL,
                        schema_version VARCHAR(20) NOT NULL,
                        payload JSONB NOT NULL,
                        trace JSONB,
                        received_at TIMESTAMP NOT NULL DEFAULT NOW(),
                        status VARCHAR(20) NOT NULL DEFAULT 'received'
                    )
                    """
                )
            conn.commit()

    @classmethod
    def list_states(cls) -> list[dict]:
        cls._ensure_table()
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT clave, nombre, descripcion, encendido, updated_by, updated_at
                    FROM public.control_hardware_estado
                    ORDER BY nombre ASC
                    """
                )
                rows = cur.fetchall()

        return [
            {
                "clave": row[0],
                "nombre": row[1],
                "descripcion": row[2] or "",
                "encendido": bool(row[3]),
                "updated_by": row[4],
                "updated_at": row[5],
            }
            for row in rows
        ]

    @classmethod
    def update_states(cls, state_map: dict[str, bool], user_id: int | None = None) -> None:
        cls._ensure_table()
        if not state_map:
            return

        with get_connection() as conn:
            with conn.cursor() as cur:
                for clave, encendido in state_map.items():
                    cur.execute(
                        """
                        UPDATE public.control_hardware_estado
                        SET encendido = %s,
                            updated_by = %s,
                            updated_at = NOW()
                        WHERE clave = %s
                        """,
                        (bool(encendido), user_id, clave),
                    )
            conn.commit()

    @classmethod
    def update_one(cls, clave: str, encendido: bool, user_id: int | None = None) -> bool:
        cls._ensure_table()
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE public.control_hardware_estado
                    SET encendido = %s,
                        updated_by = %s,
                        updated_at = NOW()
                    WHERE clave = %s
                    """,
                    (bool(encendido), user_id, clave),
                )
                updated = cur.rowcount
            conn.commit()
        return updated > 0

    @classmethod
    def register_event(
        cls,
        event_id: str,
        event_type: str,
        source_device: str,
        occurred_at,
        schema_version: str,
        payload: dict,
        trace: dict | None = None,
    ) -> bool:
        cls._ensure_events_table()
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO public.control_hardware_eventos (
                        event_id, event_type, source_device, occurred_at, schema_version, payload, trace
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (event_id) DO NOTHING
                    """,
                    (
                        event_id,
                        event_type,
                        source_device,
                        occurred_at,
                        schema_version,
                        Json(payload or {}),
                        Json(trace) if isinstance(trace, dict) else None,
                    ),
                )
                inserted = cur.rowcount
            conn.commit()
        return inserted > 0

    @classmethod
    def list_recent_events(cls, limit: int = 50) -> list[dict]:
        cls._ensure_events_table()
        safe_limit = max(1, min(int(limit or 50), 300))

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        event_id,
                        event_type,
                        source_device,
                        occurred_at,
                        schema_version,
                        payload,
                        status,
                        received_at
                    FROM public.control_hardware_eventos
                    ORDER BY received_at DESC
                    LIMIT %s
                    """,
                    (safe_limit,),
                )
                rows = cur.fetchall()

        events = []
        for row in rows:
            payload = row[5] if isinstance(row[5], dict) else {}
            events.append(
                {
                    "event_id": row[0],
                    "event_type": row[1],
                    "source_device": row[2],
                    "occurred_at": row[3],
                    "schema_version": row[4],
                    "payload": payload,
                    "placa": str(payload.get("placa") or "").strip().upper(),
                    "status": row[6],
                    "received_at": row[7],
                }
            )

        return events

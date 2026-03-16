"""Sincronización Web -> BD local (RF18).

Estrategia:
1) Intenta replicar en tiempo real hacia BD local.
2) Si falla, guarda pendiente en BD web (public.sync_pendientes_local).
3) En cada operación exitosa, reintenta pendientes.
4) Registra respaldo de eventos en BD local (public.sync_eventos_web).
"""

from __future__ import annotations

from datetime import date, datetime
import json
from typing import Any

from flask import current_app
from psycopg2 import sql
from psycopg2.extras import Json

from app.db import get_connection, get_local_connection


class LocalSyncService:
    @staticmethod
    def _json_default(value: Any):
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        return str(value)

    @classmethod
    def _normalize_payload(cls, payload: dict) -> dict:
        normalized = {}
        for key, value in (payload or {}).items():
            if isinstance(value, (dict, list)):
                normalized[key] = json.loads(json.dumps(value, default=cls._json_default))
            elif isinstance(value, (datetime, date)):
                normalized[key] = value.isoformat()
            else:
                normalized[key] = value
        return normalized

    @staticmethod
    def _ensure_web_pending_table() -> None:
        query = """
            CREATE TABLE IF NOT EXISTS public.sync_pendientes_local (
                id BIGSERIAL PRIMARY KEY,
                entidad VARCHAR(80) NOT NULL,
                operacion VARCHAR(40) NOT NULL,
                payload JSONB NOT NULL,
                intentos INTEGER NOT NULL DEFAULT 0,
                estado VARCHAR(20) NOT NULL DEFAULT 'pendiente',
                ultimo_error TEXT,
                created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP NOT NULL DEFAULT NOW()
            )
        """
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query)
            conn.commit()

    @staticmethod
    def _ensure_local_event_table(local_conn) -> None:
        query = """
            CREATE TABLE IF NOT EXISTS public.sync_eventos_web (
                id BIGSERIAL PRIMARY KEY,
                entidad VARCHAR(80) NOT NULL,
                operacion VARCHAR(40) NOT NULL,
                payload JSONB NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT NOW()
            )
        """
        with local_conn.cursor() as cur:
            cur.execute(query)

    @staticmethod
    def _get_local_columns(local_conn, table_name: str) -> set[str]:
        query = """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = %s
        """
        with local_conn.cursor() as cur:
            cur.execute(query, (table_name,))
            return {row[0] for row in cur.fetchall()}

    @classmethod
    def _sync_vehiculo(cls, local_conn, payload: dict) -> None:
        cols = cls._get_local_columns(local_conn, "vehiculos")
        if not cols:
            return

        data = {k: v for k, v in payload.items() if k in cols}
        placa = (data.get("placa") or "").strip().upper()
        if not placa:
            return
        data["placa"] = placa

        update_keys = [k for k in data.keys() if k != "placa"]
        if update_keys:
            update_query = sql.SQL("UPDATE public.vehiculos SET {assignments} WHERE upper(placa)=upper(%s)").format(
                assignments=sql.SQL(", ").join(
                    sql.SQL("{} = {}" ).format(sql.Identifier(k), sql.Placeholder()) for k in update_keys
                )
            )
            update_values = [data[k] for k in update_keys] + [placa]
            with local_conn.cursor() as cur:
                cur.execute(update_query, update_values)
                updated = cur.rowcount
        else:
            updated = 0

        if updated > 0:
            return

        insert_keys = list(data.keys())
        insert_query = sql.SQL("INSERT INTO public.vehiculos ({fields}) VALUES ({values})").format(
            fields=sql.SQL(", ").join(sql.Identifier(k) for k in insert_keys),
            values=sql.SQL(", ").join(sql.Placeholder() for _ in insert_keys),
        )
        insert_values = [data[k] for k in insert_keys]
        with local_conn.cursor() as cur:
            cur.execute(insert_query, insert_values)

    @classmethod
    def _sync_novedad(cls, local_conn, payload: dict) -> None:
        cols = cls._get_local_columns(local_conn, "novedad")
        if not cols:
            return

        data = {k: v for k, v in payload.items() if k in cols}
        if not data:
            return

        insert_keys = list(data.keys())
        insert_query = sql.SQL("INSERT INTO public.novedad ({fields}) VALUES ({values})").format(
            fields=sql.SQL(", ").join(sql.Identifier(k) for k in insert_keys),
            values=sql.SQL(", ").join(sql.Placeholder() for _ in insert_keys),
        )
        insert_values = [data[k] for k in insert_keys]
        with local_conn.cursor() as cur:
            cur.execute(insert_query, insert_values)

    @classmethod
    def _apply_to_local(cls, entidad: str, operacion: str, payload: dict) -> None:
        local_payload = cls._normalize_payload(payload)
        with get_local_connection() as local_conn:
            cls._ensure_local_event_table(local_conn)

            if entidad == "vehiculos":
                cls._sync_vehiculo(local_conn, local_payload)
            elif entidad == "novedad":
                cls._sync_novedad(local_conn, local_payload)

            with local_conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO public.sync_eventos_web (entidad, operacion, payload) VALUES (%s, %s, %s)",
                    (entidad, operacion, Json(local_payload)),
                )
            local_conn.commit()

    @classmethod
    def enqueue_pending(cls, entidad: str, operacion: str, payload: dict, error_text: str = "") -> None:
        cls._ensure_web_pending_table()
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO public.sync_pendientes_local (entidad, operacion, payload, estado, ultimo_error)
                    VALUES (%s, %s, %s, 'pendiente', %s)
                    """,
                    (entidad, operacion, Json(cls._normalize_payload(payload)), (error_text or "")[:1500]),
                )
            conn.commit()

    @classmethod
    def retry_pending(cls, limit: int = 30) -> dict:
        cls._ensure_web_pending_table()
        max_retries = int(current_app.config.get("SYNC_MAX_RETRIES", 10))
        processed = 0
        sent = 0
        failed = 0

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, entidad, operacion, payload, intentos
                    FROM public.sync_pendientes_local
                    WHERE estado = 'pendiente'
                    ORDER BY created_at ASC
                    LIMIT %s
                    """,
                    (limit,),
                )
                rows = cur.fetchall()

            for row in rows:
                pending_id, entidad, operacion, payload, intentos = row
                processed += 1
                try:
                    cls._apply_to_local(entidad=entidad, operacion=operacion, payload=payload or {})
                    with conn.cursor() as cur:
                        cur.execute(
                            """
                            UPDATE public.sync_pendientes_local
                            SET estado = 'enviado', updated_at = NOW(), ultimo_error = NULL
                            WHERE id = %s
                            """,
                            (pending_id,),
                        )
                    conn.commit()
                    sent += 1
                except Exception as exc:
                    with conn.cursor() as cur:
                        cur.execute(
                            """
                            UPDATE public.sync_pendientes_local
                            SET intentos = %s,
                                ultimo_error = %s,
                                updated_at = NOW(),
                                estado = CASE WHEN %s >= %s THEN 'fallido' ELSE 'pendiente' END
                            WHERE id = %s
                            """,
                            (intentos + 1, str(exc)[:1500], intentos + 1, max_retries, pending_id),
                        )
                    conn.commit()
                    failed += 1

        return {"processed": processed, "sent": sent, "failed": failed}

    @classmethod
    def sync_event(cls, entidad: str, operacion: str, payload: dict) -> dict:
        try:
            cls._apply_to_local(entidad=entidad, operacion=operacion, payload=payload)
            retry_report = cls.retry_pending(limit=20)
            return {"ok": True, "queued": False, "retry": retry_report}
        except Exception as exc:
            cls.enqueue_pending(entidad=entidad, operacion=operacion, payload=payload, error_text=str(exc))
            return {"ok": False, "queued": True, "error": str(exc)}

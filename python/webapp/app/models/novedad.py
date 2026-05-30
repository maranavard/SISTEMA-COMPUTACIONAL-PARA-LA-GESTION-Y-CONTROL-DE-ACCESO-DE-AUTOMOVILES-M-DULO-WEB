"""Modelo de novedades para control de ingreso/salida por placa."""

from datetime import datetime
from zoneinfo import ZoneInfo

from psycopg2 import sql

import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    """Obtiene conexión directa a Neon PostgreSQL."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("❌ DATABASE_URL no configurada")
    return psycopg2.connect(dsn=database_url, sslmode="require")


from app.models.espacio import Espacio
from app.utils.local_sync import LocalSyncService


class Novedad:
    @staticmethod
    def _now_local() -> datetime:
        return datetime.now(ZoneInfo("America/Bogota")).replace(tzinfo=None)

    @staticmethod
    def _get_columns() -> set[str]:
        query = """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = 'novedad'
        """
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                return {row[0] for row in cur.fetchall()}

    @staticmethod
    def _find_vehicle_id_by_plate(placa: str) -> int | None:
        query = """
            SELECT id
            FROM public.vehiculos
            WHERE upper(placa) = upper(%s)
            LIMIT 1
        """
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (placa,))
                row = cur.fetchone()
        return row[0] if row else None

    @staticmethod
    def _find_vehicle_by_plate(placa: str) -> tuple[int, int | None] | None:
        query = """
            SELECT id, tipo_vehiculo_id
            FROM public.vehiculos
            WHERE upper(placa) = upper(%s)
            LIMIT 1
        """
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (placa,))
                row = cur.fetchone()

        if not row:
            return None
        return row[0], row[1]

    @staticmethod
    def _find_open_space_for_vehicle(vehicle_tipo_id: int | None) -> dict | None:
        slots = Espacio.build_slots(total_slots=50)
        disponibles = [
            slot
            for slot in slots
            if slot.get("estado") == "disponible"
            and (slot.get("tipo_vehiculo_id") in (None, vehicle_tipo_id))
        ]

        if not disponibles:
            return None

        return min(disponibles, key=lambda item: int(item.get("numero") or 0))

    @classmethod
    def _insert_novedad(cls, payload: dict) -> int | None:
        cols = cls._get_columns()

        field_order = [
            "tipo_novedad",
            "id_vehiculo",
            "id_espacio",
            "fecha_hora",
            "id_usuario",
            "observaciones",
            "estado",
        ]

        insert_cols = []
        insert_vals = []

        for field in field_order:
            if field not in cols:
                continue
            value = payload.get(field)
            if value is None or value == "":
                continue
            insert_cols.append(field)
            insert_vals.append(value)

        if not insert_cols:
            return None

        query = sql.SQL("INSERT INTO public.novedad ({fields}) VALUES ({values}) RETURNING id").format(
            fields=sql.SQL(", ").join(sql.Identifier(column_name) for column_name in insert_cols),
            values=sql.SQL(", ").join(sql.Placeholder() for _ in insert_cols),
        )

        inserted_id = None
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, insert_vals)
                row = cur.fetchone()
                inserted_id = row[0] if row else None
            conn.commit()

        return inserted_id

    @staticmethod
    def list_recent(limit: int = 50) -> list[dict]:
        query = """
            SELECT
                n.id,
                n.tipo_novedad,
                n.id_vehiculo,
                v.placa,
                n.id_espacio,
                e.numero AS espacio_numero,
                n.id_usuario,
                n.estado,
                n.fecha_hora,
                n.observaciones
            FROM public.novedad n
            LEFT JOIN public.vehiculos v ON v.id = n.id_vehiculo
            LEFT JOIN public.espacio e ON e.id_espacio = n.id_espacio
            ORDER BY n.fecha_hora DESC, n.id DESC
            LIMIT %s
        """

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (limit,))
                rows = cur.fetchall()

        return [
            {
                "id": row[0],
                "tipo_novedad": row[1],
                "id_vehiculo": row[2],
                "placa": row[3],
                "id_espacio": row[4],
                "espacio_numero": row[5],
                "id_usuario": row[6],
                "estado": row[7],
                "fecha_hora": row[8],
                "observaciones": row[9],
            }
            for row in rows
        ]


          @staticmethod
    def search_access_history(placa: str = "", fecha: str = "", documento: str = "") -> list[dict]:
        placa = (placa or "").strip().upper()
        fecha = (fecha or "").strip()
        documento = (documento or "").strip().lower()

        conditions = []
        params = []

        if placa:
            conditions.append("upper(v.placa) LIKE %s")
            params.append(f"%{placa}%")

        if fecha:
            conditions.append("DATE(n.fecha_hora) = %s")
            params.append(fecha)

        if documento:
            conditions.append(
                """
                (
                    lower(coalesce(u.numero_identificacion, '')) LIKE %s
                    OR lower(coalesce(u.identificacion, '')) LIKE %s
                    OR lower(coalesce(u.documento, '')) LIKE %s
                    OR lower(coalesce(u.cedula, '')) LIKE %s
                )
                """
            )
            like_doc = f"%{documento}%"
            params.extend([like_doc, like_doc, like_doc, like_doc])

        where_sql = ""
        if conditions:
            where_sql = "WHERE " + " AND ".join(conditions)

        query = f"""
            SELECT
                n.id,
                n.tipo_novedad,
                n.id_vehiculo,
                v.placa,
                n.id_espacio,
                e.numero AS espacio_numero,
                n.id_usuario,
                u.username,
                COALESCE(
                    u.numero_identificacion,
                    u.identificacion,
                    u.documento,
                    u.cedula,
                    ''
                ) AS documento_usuario,
                n.estado,
                n.fecha_hora,
                n.observaciones
            FROM public.novedad n
            LEFT JOIN public.vehiculos v ON v.id = n.id_vehiculo
            LEFT JOIN public.espacio e ON e.id_espacio = n.id_espacio
            LEFT JOIN public.usuarios u ON u.id = n.id_usuario
            {where_sql}
            ORDER BY n.fecha_hora DESC, n.id DESC
        """

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                rows = cur.fetchall()

        return [
            {
                "id": row[0],
                "tipo_novedad": row[1],
                "id_vehiculo": row[2],
                "placa": row[3],
                "id_espacio": row[4],
                "espacio_numero": row[5],
                "id_usuario": row[6],
                "username": row[7],
                "documento_usuario": row[8],
                "estado": row[9],
                "fecha_hora": row[10],
                "observaciones": row[11],
            }
            for row in rows
        ]
    
    
    @classmethod
    def register_ingreso_by_placa(cls, placa: str, user_id: int) -> dict:
        vehicle = cls._find_vehicle_by_plate(placa)
        if not vehicle:
            raise ValueError(f"No existe vehículo con placa {placa}")

        vehicle_id, vehicle_tipo_id = vehicle

        slot = cls._find_open_space_for_vehicle(vehicle_tipo_id)
        if not slot:
            return {"assigned_space_id": None, "assigned_space_num": None}

        slot_numero = str(slot.get("numero"))
        Espacio.upsert_by_numero(
            {
                "numero": slot_numero,
                "estado": "ocupado",
                "tipo_vehiculo_id": str(vehicle_tipo_id) if vehicle_tipo_id is not None else "",
            }
        )

        espacio = Espacio.get_by_numero(slot_numero)
        espacio_id = int(espacio["id"]) if espacio and espacio.get("id") is not None else None

        payload = {
            "tipo_novedad": "ingreso",
            "id_vehiculo": vehicle_id,
            "id_espacio": espacio_id,
            "fecha_hora": cls._now_local(),
            "id_usuario": user_id,
            "observaciones": "Ingreso automático web",
            "estado": "registrado",
        }

        inserted_id = cls._insert_novedad(payload)
        if inserted_id is None:
            raise ValueError("No se pudo registrar el ingreso en la tabla de novedades.")

        try:
            LocalSyncService.sync_event(entidad="novedad", operacion="insert", payload=payload)
        except Exception:
            pass

        return {"assigned_space_id": espacio_id, "assigned_space_num": slot_numero}

    @staticmethod
    def register_salida_by_placa(
        placa: str,
        user_id: int,
        observaciones: str = "Salida manual web",
        espacio_numero: str | None = None,
    ) -> int:
        now_local = Novedad._now_local()
        vehicle = Novedad._find_vehicle_by_plate(placa)
        if not vehicle:
            raise ValueError(f"No existe vehículo con placa {placa}")

        vehicle_id, _ = vehicle

        espacio_id = None
        espacio = None

        if espacio_numero:
            espacio = Espacio.get_by_numero(str(espacio_numero).strip())
            if espacio and espacio.get("id") is not None:
                espacio_id = int(espacio["id"])

        if espacio_id is None:
            latest_ingreso_query = """
                SELECT n.id_espacio
                FROM public.novedad n
                WHERE n.id_vehiculo = %s
                  AND lower(coalesce(n.tipo_novedad, '')) IN ('ingreso', 'entrada')
                  AND n.id_espacio IS NOT NULL
                ORDER BY n.fecha_hora DESC, n.id DESC
                LIMIT 1
            """
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(latest_ingreso_query, (vehicle_id,))
                    row_ingreso = cur.fetchone()
                    espacio_id = row_ingreso[0] if row_ingreso else None

        payload = {
            "tipo_novedad": "salida",
            "id_vehiculo": vehicle_id,
            "id_espacio": espacio_id,
            "fecha_hora": now_local,
            "id_usuario": user_id,
            "observaciones": observaciones,
            "estado": "registrado",
        }

        inserted_id = Novedad._insert_novedad(payload)
        if inserted_id is None:
            raise ValueError(f"No se pudo registrar salida para la placa {placa}")

        if espacio_id is not None:
            if espacio is None:
                espacio = Espacio.get_by_id(int(espacio_id))

            if espacio and espacio.get("numero") is not None:
                Espacio.upsert_by_numero(
                    {
                        "numero": str(espacio.get("numero")),
                        "estado": "disponible",
                        "tipo_vehiculo_id": espacio.get("tipo_vehiculo_id") or "",
                    }
                )

        try:
            LocalSyncService.sync_event(entidad="novedad", operacion="insert", payload=payload)
        except Exception:
            pass

        return inserted_id

    @classmethod
    def create_reporte(cls, payload: dict) -> int:
        cols = cls._get_columns()
        placa = (payload.get("placa") or "").strip().upper()

        if "id_vehiculo" in cols:
            if not placa:
                raise ValueError("Debes indicar la placa del vehículo")
            vehicle_id = cls._find_vehicle_id_by_plate(placa)
            if not vehicle_id:
                raise ValueError(f"No existe vehículo con placa {placa}")
            payload["id_vehiculo"] = vehicle_id

        insert_cols = []
        insert_vals = []

        field_order = [
            "tipo_novedad",
            "id_vehiculo",
            "fecha_hora",
            "id_usuario",
            "observaciones",
            "estado",
        ]

        for field in field_order:
            if field not in cols:
                continue
            value = payload.get(field)
            if value in (None, ""):
                continue
            insert_cols.append(field)
            insert_vals.append(value)

        if "tipo_novedad" in cols and "tipo_novedad" not in insert_cols:
            insert_cols.append("tipo_novedad")
            insert_vals.append("novedad")

        query = sql.SQL("INSERT INTO public.novedad ({fields}) VALUES ({values}) RETURNING id").format(
            fields=sql.SQL(", ").join(sql.Identifier(column_name) for column_name in insert_cols),
            values=sql.SQL(", ").join(sql.Placeholder() for _ in insert_cols),
        )

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, insert_vals)
                row = cur.fetchone()
            conn.commit()

        try:
            LocalSyncService.sync_event(entidad="novedad", operacion="insert", payload=payload)
        except Exception:
            pass

        return row[0]

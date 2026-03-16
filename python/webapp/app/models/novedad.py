"""Modelo de novedades para control de ingreso/salida por placa."""

from datetime import datetime

from psycopg2 import sql

from app.db import get_connection
from app.models.espacio import Espacio
from app.utils.local_sync import LocalSyncService


class Novedad:
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
    def register_ingreso_by_placa(placa: str, user_id: int) -> dict:
        row = None
        sql_error = None

        query = "SELECT assigned_space_id, assigned_space_num FROM public.assign_space_and_register_ingreso(%s, %s)"
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, (placa, user_id))
                    row = cur.fetchone()
                conn.commit()
        except Exception as exc:
            sql_error = exc

        if row and row[0] is not None:
            try:
                vehicle_id = Novedad._find_vehicle_id_by_plate(placa)
                LocalSyncService.sync_event(
                    entidad="novedad",
                    operacion="insert",
                    payload={
                        "tipo_novedad": "ingreso",
                        "id_vehiculo": vehicle_id,
                        "id_usuario": user_id,
                        "id_espacio": row[0],
                        "fecha_hora": datetime.now(),
                        "observaciones": "Ingreso automático sincronizado",
                        "estado": "registrado",
                    },
                )
            except Exception:
                pass
            return {"assigned_space_id": row[0], "assigned_space_num": row[1]}

        fallback = Novedad._assign_space_manual_fallback(placa=placa, user_id=user_id)
        if fallback:
            return fallback

        if sql_error:
            raise sql_error

        return {"assigned_space_id": None, "assigned_space_num": None}

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

    @classmethod
    def _insert_ingreso_novedad(
        cls,
        vehicle_id: int,
        user_id: int,
        espacio_id: int | None,
        observaciones: str,
    ) -> int | None:
        cols = cls._get_columns()
        payload = {
            "tipo_novedad": "ingreso",
            "id_vehiculo": vehicle_id,
            "id_espacio": espacio_id,
            "fecha_hora": datetime.now(),
            "id_usuario": user_id,
            "observaciones": observaciones,
            "estado": "registrado",
        }

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

                if inserted_id is not None and espacio_id is not None:
                    cur.execute(
                        "UPDATE public.novedad SET id_espacio = %s WHERE id = %s",
                        (espacio_id, inserted_id),
                    )
            conn.commit()

        try:
            LocalSyncService.sync_event(entidad="novedad", operacion="insert", payload=payload)
        except Exception:
            pass

        return inserted_id

    @classmethod
    def _assign_space_manual_fallback(cls, placa: str, user_id: int) -> dict:
        vehicle = cls._find_vehicle_by_plate(placa)
        if not vehicle:
            raise ValueError(f"No existe vehículo con placa {placa}")

        vehicle_id, vehicle_tipo_id = vehicle

        slots = Espacio.build_slots(total_slots=50)
        disponibles = [
            slot
            for slot in slots
            if slot.get("estado") == "disponible"
            and (slot.get("tipo_vehiculo_id") in (None, vehicle_tipo_id))
        ]

        if not disponibles:
            return {"assigned_space_id": None, "assigned_space_num": None}

        slot = sorted(disponibles, key=lambda item: int(item.get("numero") or 0))[0]
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

        cls._insert_ingreso_novedad(
            vehicle_id=vehicle_id,
            user_id=user_id,
            espacio_id=espacio_id,
            observaciones="Ingreso automático (respaldo manual web)",
        )

        return {
            "assigned_space_id": espacio_id,
            "assigned_space_num": slot_numero,
        }

    @staticmethod
    def register_salida_by_placa(placa: str, user_id: int, observaciones: str = "Salida manual web") -> int:
        query = """
            INSERT INTO public.novedad (tipo_novedad, id_vehiculo, fecha_hora, id_usuario, observaciones)
            SELECT 'salida', v.id, NOW(), %s, %s
            FROM public.vehiculos v
            WHERE upper(v.placa) = upper(%s)
            LIMIT 1
            RETURNING id
        """

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (user_id, observaciones, placa))
                row = cur.fetchone()
            conn.commit()

        if not row:
            raise ValueError(f"No existe vehículo con placa {placa}")

        try:
            vehicle_id = Novedad._find_vehicle_id_by_plate(placa)
            LocalSyncService.sync_event(
                entidad="novedad",
                operacion="insert",
                payload={
                    "tipo_novedad": "salida",
                    "id_vehiculo": vehicle_id,
                    "id_usuario": user_id,
                    "fecha_hora": datetime.now(),
                    "observaciones": observaciones,
                    "estado": "registrado",
                },
            )
        except Exception:
            pass

        return row[0]

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

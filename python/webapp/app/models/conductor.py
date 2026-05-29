"""Modelo de conductores compatible con distintos esquemas existentes.

Soporta tablas `public.conductores` o `public.conductors`.
"""

from __future__ import annotations

import os

import psycopg2
from dotenv import load_dotenv
from psycopg2 import sql

load_dotenv()


def get_connection():
    """Obtiene conexión directa a Neon PostgreSQL."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("❌ DATABASE_URL no configurada")
    return psycopg2.connect(dsn=database_url, sslmode="require")


class Conductor:
    @staticmethod
    def _get_table_name() -> str:
        query = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
              AND table_name IN ('conductores', 'conductors')
            ORDER BY CASE table_name WHEN 'conductores' THEN 0 ELSE 1 END
            LIMIT 1
        """
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                row = cur.fetchone()
        return row[0] if row else "conductores"

    @staticmethod
    def _get_columns(table_name: str) -> set[str]:
        query = """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = %s
        """
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (table_name,))
                return {row[0] for row in cur.fetchall()}

    @staticmethod
    def _pick_id_column(cols: set[str]) -> str | None:
        if "id" in cols:
            return "id"
        if "id_conductor" in cols:
            return "id_conductor"
        return None

    @staticmethod
    def _pick_fecha_vencimiento_column(cols: set[str]) -> str | None:
        if "fecha_vencimiento_pase" in cols:
            return "fecha_vencimiento_pase"
        if "fecha_vencimiento_pas" in cols:
            return "fecha_vencimiento_pas"
        return None

    @classmethod
    def get_by_user_id(cls, user_id: int) -> dict | None:
        table_name = cls._get_table_name()
        cols = cls._get_columns(table_name)
        id_col = cls._pick_id_column(cols)

        if not id_col or "user_id" not in cols:
            return None

        fecha_vencimiento_col = cls._pick_fecha_vencimiento_column(cols)

        select_map = {
            "id": f"c.{id_col}",
            "user_id": "c.user_id",
            "nombre": "c.nombre" if "nombre" in cols else "NULL::text AS nombre",
            "apellido": "c.apellido" if "apellido" in cols else "NULL::text AS apellido",
            "cedula": "c.cedula" if "cedula" in cols else "NULL::text AS cedula",
            "email": "c.email" if "email" in cols else "NULL::text AS email",
            "telefono": "c.telefono" if "telefono" in cols else "NULL::text AS telefono",
            "dependencia": "c.dependencia" if "dependencia" in cols else "NULL::text AS dependencia",
            "tipo": "c.tipo" if "tipo" in cols else "NULL::text AS tipo",
            "estado": "c.estado" if "estado" in cols else "'activo'::text AS estado",
            "numero_pase": "c.numero_pase" if "numero_pase" in cols else "NULL::text AS numero_pase",
            "categoria_pase": "c.categoria_pase" if "categoria_pase" in cols else "NULL::text AS categoria_pase",
            "fecha_registro": "c.fecha_registro" if "fecha_registro" in cols else "NULL::timestamp AS fecha_registro",
            "fecha_vencimiento_pase": (
                f"c.{fecha_vencimiento_col}"
                if fecha_vencimiento_col
                else "NULL::date AS fecha_vencimiento_pase"
            ),
        }

        query = f"""
            SELECT
                {select_map['id']},
                {select_map['user_id']},
                {select_map['nombre']},
                {select_map['apellido']},
                {select_map['cedula']},
                {select_map['email']},
                {select_map['telefono']},
                {select_map['dependencia']},
                {select_map['tipo']},
                {select_map['estado']},
                {select_map['numero_pase']},
                {select_map['categoria_pase']},
                {select_map['fecha_registro']},
                {select_map['fecha_vencimiento_pase']}
            FROM public.{table_name} c
            WHERE c.user_id = %s
            LIMIT 1
        """

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (user_id,))
                row = cur.fetchone()

        if not row:
            return None

        return {
            "id": row[0],
            "user_id": row[1],
            "nombre": row[2],
            "apellido": row[3],
            "cedula": row[4],
            "email": row[5],
            "telefono": row[6],
            "dependencia": row[7],
            "tipo": row[8],
            "estado": row[9],
            "numero_pase": row[10],
            "categoria_pase": row[11],
            "fecha_registro": row[12],
            "fecha_vencimiento_pase": row[13],
        }

    @classmethod
    def list_items(cls) -> list[dict]:
        table_name = cls._get_table_name()
        cols = cls._get_columns(table_name)
        id_col = cls._pick_id_column(cols)
        if not id_col:
            raise ValueError(f"La tabla {table_name} no tiene columna identificadora soportada.")

        fecha_vencimiento_col = cls._pick_fecha_vencimiento_column(cols)

        select_map = {
            "id": f"c.{id_col}",
            "nombre": "c.nombre" if "nombre" in cols else "NULL::text AS nombre",
            "apellido": "c.apellido" if "apellido" in cols else "NULL::text AS apellido",
            "cedula": "c.cedula" if "cedula" in cols else "NULL::text AS cedula",
            "email": "c.email" if "email" in cols else "NULL::text AS email",
            "telefono": "c.telefono" if "telefono" in cols else "NULL::text AS telefono",
            "dependencia": "c.dependencia" if "dependencia" in cols else "NULL::text AS dependencia",
            "tipo": "c.tipo" if "tipo" in cols else "NULL::text AS tipo",
            "estado": "c.estado" if "estado" in cols else "'activo'::text AS estado",
            "numero_pase": "c.numero_pase" if "numero_pase" in cols else "NULL::text AS numero_pase",
            "categoria_pase": "c.categoria_pase" if "categoria_pase" in cols else "NULL::text AS categoria_pase",
            "fecha_registro": "c.fecha_registro" if "fecha_registro" in cols else "NULL::timestamp AS fecha_registro",
            "fecha_vencimiento_pase": (
                f"c.{fecha_vencimiento_col}"
                if fecha_vencimiento_col
                else "NULL::date AS fecha_vencimiento_pase"
            ),
        }

        query = f"""
            SELECT
                {select_map['id']},
                {select_map['nombre']},
                {select_map['apellido']},
                {select_map['cedula']},
                {select_map['email']},
                {select_map['telefono']},
                {select_map['dependencia']},
                {select_map['tipo']},
                {select_map['estado']},
                {select_map['numero_pase']},
                {select_map['categoria_pase']},
                {select_map['fecha_registro']},
                {select_map['fecha_vencimiento_pase']}
            FROM public.{table_name} c
            ORDER BY c.{id_col} DESC
        """

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                rows = cur.fetchall()

        return [
            {
                "id": row[0],
                "nombre": row[1],
                "apellido": row[2],
                "cedula": row[3],
                "email": row[4],
                "telefono": row[5],
                "dependencia": row[6],
                "tipo": row[7],
                "estado": row[8],
                "numero_pase": row[9],
                "categoria_pase": row[10],
                "fecha_registro": row[11],
                "fecha_vencimiento_pase": row[12],
            }
            for row in rows
        ]

    @classmethod
    def create_item(cls, data: dict) -> None:
        table_name = cls._get_table_name()
        cols = cls._get_columns(table_name)
        fecha_vencimiento_col = cls._pick_fecha_vencimiento_column(cols)

        allowed_fields = [
            "user_id",
            "nombre",
            "apellido",
            "cedula",
            "email",
            "telefono",
            "dependencia",
            "tipo",
            "estado",
            "numero_pase",
            "categoria_pase",
            "fecha_registro",
        ]

        payload = dict(data)
        if fecha_vencimiento_col and payload.get("fecha_vencimiento_pase") not in (None, ""):
            payload[fecha_vencimiento_col] = payload.get("fecha_vencimiento_pase")
            allowed_fields.append(fecha_vencimiento_col)

        insert_cols = []
        insert_vals = []
        for field in allowed_fields:
            if field in cols and payload.get(field) not in (None, ""):
                insert_cols.append(field)
                insert_vals.append(payload[field])

        if not insert_cols:
            return

        query = sql.SQL("INSERT INTO public.{table} ({fields}) VALUES ({values})").format(
            table=sql.Identifier(table_name),
            fields=sql.SQL(", ").join(sql.Identifier(c) for c in insert_cols),
            values=sql.SQL(", ").join(sql.Placeholder() for _ in insert_cols),
        )

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, insert_vals)
            conn.commit()

    @classmethod
    def update_item(cls, item_id: int, data: dict) -> None:
        table_name = cls._get_table_name()
        cols = cls._get_columns(table_name)
        id_col = cls._pick_id_column(cols)
        if not id_col:
            raise ValueError(f"La tabla {table_name} no tiene columna identificadora soportada.")

        fecha_vencimiento_col = cls._pick_fecha_vencimiento_column(cols)

        allowed_fields = [
            "user_id",
            "nombre",
            "apellido",
            "cedula",
            "email",
            "telefono",
            "dependencia",
            "tipo",
            "estado",
            "numero_pase",
            "categoria_pase",
            "fecha_registro",
        ]

        payload = dict(data)
        if fecha_vencimiento_col and "fecha_vencimiento_pase" in payload:
            payload[fecha_vencimiento_col] = payload.get("fecha_vencimiento_pase")
            allowed_fields.append(fecha_vencimiento_col)

        assignments = []
        values = []
        for field in allowed_fields:
            if field in cols and field in payload:
                assignments.append(sql.SQL("{} = {}").format(sql.Identifier(field), sql.Placeholder()))
                values.append(payload[field] if payload[field] != "" else None)

        if not assignments:
            return

        values.append(item_id)
        query = sql.SQL("UPDATE public.{table} SET {assignments} WHERE {id_col} = %s").format(
            table=sql.Identifier(table_name),
            assignments=sql.SQL(", ").join(assignments),
            id_col=sql.Identifier(id_col),
        )

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, values)
            conn.commit()

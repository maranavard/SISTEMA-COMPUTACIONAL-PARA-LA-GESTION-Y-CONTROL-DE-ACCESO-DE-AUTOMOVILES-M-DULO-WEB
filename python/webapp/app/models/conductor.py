"""Modelo de conductores compatible con distintos esquemas existentes.

Soporta tablas `public.conductores` o `public.conductors`.
"""

from psycopg2 import sql

from app.db import get_connection


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

    @classmethod
    def list_items(cls) -> list[dict]:
        table_name = cls._get_table_name()
        cols = cls._get_columns(table_name)

        select_map = {
            "id": "c.id",
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
            "fecha_vencimiento_pase": "c.fecha_vencimiento_pase" if "fecha_vencimiento_pase" in cols else "NULL::date AS fecha_vencimiento_pase",
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
            ORDER BY c.id DESC
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

        allowed_fields = [
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
            "fecha_vencimiento_pase",
        ]

        insert_cols = []
        insert_vals = []
        for field in allowed_fields:
            if field in cols and data.get(field) not in (None, ""):
                insert_cols.append(field)
                insert_vals.append(data[field])

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

        allowed_fields = [
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
            "fecha_vencimiento_pase",
        ]

        assignments = []
        values = []
        for field in allowed_fields:
            if field in cols and field in data:
                assignments.append(sql.SQL("{} = {}").format(sql.Identifier(field), sql.Placeholder()))
                values.append(data[field] if data[field] != "" else None)

        if not assignments:
            return

        values.append(item_id)
        query = sql.SQL("UPDATE public.{table} SET {assignments} WHERE id = %s").format(
            table=sql.Identifier(table_name),
            assignments=sql.SQL(", ").join(assignments),
        )

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, values)
            conn.commit()

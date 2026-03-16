"""Modelo de visitantes compatible con distintos esquemas existentes.

Soporta tablas `public.visitantes` o `public.registro_visitantes`.
"""

from psycopg2 import sql

from app.db import get_connection


class Visitante:
    @staticmethod
    def _get_table_name() -> str:
        query = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
              AND table_name IN ('visitantes', 'registro_visitantes')
            ORDER BY CASE table_name WHEN 'visitantes' THEN 0 ELSE 1 END
            LIMIT 1
        """
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                row = cur.fetchone()
        return row[0] if row else "visitantes"

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
    def _pick_existing(cols: set[str], *candidates: str) -> str | None:
        for item in candidates:
            if item in cols:
                return item
        return None

    @classmethod
    def list_items(cls) -> list[dict]:
        table_name = cls._get_table_name()
        cols = cls._get_columns(table_name)

        id_col = cls._pick_existing(cols, "id", "id_visitante", "visitante_id")
        if not id_col:
            raise ValueError(f"La tabla {table_name} no tiene columna identificadora soportada")

        nombres_col = cls._pick_existing(cols, "nombres", "nombre")
        apellidos_col = cls._pick_existing(cols, "apellidos", "apellido")
        doc_col = cls._pick_existing(cols, "numero_identificacion", "identificacion", "documento")
        area_col = cls._pick_existing(cols, "area_destino", "area")
        motivo_col = cls._pick_existing(cols, "motivo_visita", "motivo")
        placa_col = cls._pick_existing(cols, "placa")
        fecha_reg_col = cls._pick_existing(cols, "fecha_hora_registro", "fecha_registro", "fecha")
        fecha_prev_col = cls._pick_existing(cols, "fecha_hora_prevista", "fecha_prevista")
        estado_col = cls._pick_existing(cols, "estado")
        user_col = cls._pick_existing(cols, "registrado_por_usuario_id", "usuario_id", "id_usuario")

        select_map = {
            "id": f"v.{id_col} AS id",
            "nombres": f"v.{nombres_col} AS nombres" if nombres_col else "NULL::text AS nombres",
            "apellidos": f"v.{apellidos_col} AS apellidos" if apellidos_col else "NULL::text AS apellidos",
            "numero_identificacion": f"v.{doc_col} AS numero_identificacion" if doc_col else "NULL::text AS numero_identificacion",
            "area_destino": f"v.{area_col} AS area_destino" if area_col else "NULL::text AS area_destino",
            "motivo_visita": f"v.{motivo_col} AS motivo_visita" if motivo_col else "NULL::text AS motivo_visita",
            "placa": f"v.{placa_col} AS placa" if placa_col else "NULL::text AS placa",
            "fecha_hora_registro": f"v.{fecha_reg_col} AS fecha_hora_registro" if fecha_reg_col else "NULL::timestamp AS fecha_hora_registro",
            "fecha_hora_prevista": f"v.{fecha_prev_col} AS fecha_hora_prevista" if fecha_prev_col else "NULL::timestamp AS fecha_hora_prevista",
            "estado": f"v.{estado_col} AS estado" if estado_col else "NULL::text AS estado",
            "registrado_por_usuario_id": f"v.{user_col} AS registrado_por_usuario_id" if user_col else "NULL::int AS registrado_por_usuario_id",
        }

        query = f"""
            SELECT
                {select_map['id']},
                {select_map['nombres']},
                {select_map['apellidos']},
                {select_map['numero_identificacion']},
                {select_map['area_destino']},
                {select_map['motivo_visita']},
                {select_map['placa']},
                {select_map['fecha_hora_registro']},
                {select_map['fecha_hora_prevista']},
                {select_map['estado']},
                {select_map['registrado_por_usuario_id']}
            FROM public.{table_name} v
            ORDER BY v.{id_col} DESC
        """

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                rows = cur.fetchall()

        return [
            {
                "id": row[0],
                "nombres": row[1],
                "apellidos": row[2],
                "numero_identificacion": row[3],
                "area_destino": row[4],
                "motivo_visita": row[5],
                "placa": row[6],
                "fecha_hora_registro": row[7],
                "fecha_hora_prevista": row[8],
                "estado": row[9],
                "registrado_por_usuario_id": row[10],
            }
            for row in rows
        ]

    @classmethod
    def create_item(cls, data: dict) -> None:
        table_name = cls._get_table_name()
        cols = cls._get_columns(table_name)

        field_map = {
            "nombres": ["nombres", "nombre"],
            "apellidos": ["apellidos", "apellido"],
            "numero_identificacion": ["numero_identificacion", "identificacion", "documento"],
            "area_destino": ["area_destino", "area"],
            "motivo_visita": ["motivo_visita", "motivo"],
            "placa": ["placa"],
            "fecha_hora_registro": ["fecha_hora_registro", "fecha_registro", "fecha"],
            "fecha_hora_prevista": ["fecha_hora_prevista", "fecha_prevista"],
            "estado": ["estado"],
            "registrado_por_usuario_id": ["registrado_por_usuario_id", "usuario_id", "id_usuario"],
        }

        insert_cols = []
        insert_vals = []

        for key, candidates in field_map.items():
            value = data.get(key)
            if value in (None, ""):
                continue

            target_col = cls._pick_existing(cols, *candidates)
            if not target_col:
                continue

            insert_cols.append(target_col)
            insert_vals.append(value)

        if not insert_cols:
            return

        query = sql.SQL("INSERT INTO public.{table} ({fields}) VALUES ({values})").format(
            table=sql.Identifier(table_name),
            fields=sql.SQL(", ").join(sql.Identifier(column_name) for column_name in insert_cols),
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

        id_col = cls._pick_existing(cols, "id", "id_visitante", "visitante_id")
        if not id_col:
            raise ValueError(f"La tabla {table_name} no tiene columna identificadora soportada")

        field_map = {
            "nombres": ["nombres", "nombre"],
            "apellidos": ["apellidos", "apellido"],
            "numero_identificacion": ["numero_identificacion", "identificacion", "documento"],
            "area_destino": ["area_destino", "area"],
            "motivo_visita": ["motivo_visita", "motivo"],
            "placa": ["placa"],
            "fecha_hora_registro": ["fecha_hora_registro", "fecha_registro", "fecha"],
            "fecha_hora_prevista": ["fecha_hora_prevista", "fecha_prevista"],
            "estado": ["estado"],
            "registrado_por_usuario_id": ["registrado_por_usuario_id", "usuario_id", "id_usuario"],
        }

        assignments = []
        values = []

        for key, candidates in field_map.items():
            if key not in data:
                continue

            target_col = cls._pick_existing(cols, *candidates)
            if not target_col:
                continue

            assignments.append(sql.SQL("{} = {}").format(sql.Identifier(target_col), sql.Placeholder()))
            values.append(data[key] if data[key] != "" else None)

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

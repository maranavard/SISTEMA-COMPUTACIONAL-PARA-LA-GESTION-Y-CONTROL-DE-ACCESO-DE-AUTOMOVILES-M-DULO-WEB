"""Modelo de espacios compatible con distintos esquemas existentes.

Soporta tablas `public.espacio` o `public.espacios`.
"""

import re

from psycopg2 import sql

from app.db import get_connection


class Espacio:
    @staticmethod
    def _get_table_name() -> str:
        query = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
              AND table_name IN ('espacio', 'espacios')
            ORDER BY CASE table_name WHEN 'espacio' THEN 0 ELSE 1 END
            LIMIT 1
        """
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                row = cur.fetchone()
        return row[0] if row else "espacio"

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
    def _get_allowed_estado_values(cls, table_name: str) -> set[str]:
        query = """
            SELECT pg_get_constraintdef(c.oid)
            FROM pg_constraint c
            JOIN pg_class t ON t.oid = c.conrelid
            JOIN pg_namespace n ON n.oid = t.relnamespace
            WHERE n.nspname = 'public'
              AND t.relname = %s
              AND c.contype = 'c'
                            AND pg_get_constraintdef(c.oid) ILIKE '%%estado%%'
        """

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (table_name,))
                rows = cur.fetchall()

        values: set[str] = set()
        for row in rows:
            definition = row[0] or ""
            for token in re.findall(r"'([^']+)'", definition):
                if token and token.lower() != "estado":
                    values.add(token.lower())
        return values

    @classmethod
    def adapt_estado_for_db(cls, requested_estado: str) -> tuple[str, bool]:
        table_name = cls._get_table_name()
        allowed = cls._get_allowed_estado_values(table_name)

        requested = (requested_estado or "").strip().lower() or "disponible"
        if not allowed:
            return requested, False
        if requested in allowed:
            return requested, False

        logical_map = {
            "disponible": ["disponible", "libre", "dispo"],
            "ocupado": ["ocupado", "ocupada", "ocupa"],
            "inhabilitado": ["inhabilitado", "inactivo", "bloqueado", "no_disponible", "fuera_servicio"],
        }

        candidates = logical_map.get(requested, [requested])
        for candidate in candidates:
            if candidate in allowed:
                return candidate, candidate != requested

        # Fallback robusto: escoger valor más cercano por categoría
        if requested == "inhabilitado":
            for candidate in ("inactivo", "bloqueado", "ocupado", "ocupa"):
                if candidate in allowed:
                    return candidate, True
        if requested == "ocupado":
            for candidate in ("ocupa", "ocupada", "disponible", "libre"):
                if candidate in allowed:
                    return candidate, True
        if requested == "disponible":
            for candidate in ("libre", "dispo", "ocupado"):
                if candidate in allowed:
                    return candidate, True

        first = sorted(allowed)[0]
        return first, True

    @classmethod
    def list_items(cls) -> list[dict]:
        table_name = cls._get_table_name()
        cols = cls._get_columns(table_name)

        id_col = cls._pick_existing(cols, "id_espacio", "id")
        if not id_col:
            raise ValueError(f"La tabla {table_name} no tiene columna identificadora soportada")

        numero_col = cls._pick_existing(cols, "numero", "codigo", "nombre")
        estado_col = cls._pick_existing(cols, "estado")
        tipo_col = cls._pick_existing(cols, "tipo_vehiculo_id")
        fecha_col = cls._pick_existing(cols, "fecha_actualizacion", "updated_at")

        tipo_nombre_expr = (
            f"(SELECT tv.nombre FROM public.tipo_vehiculo tv WHERE tv.id = e.{tipo_col} LIMIT 1) AS tipo_vehiculo_nombre"
            if tipo_col
            else "NULL::text AS tipo_vehiculo_nombre"
        )

        select_map = {
            "id": f"e.{id_col} AS id",
            "numero": f"e.{numero_col} AS numero" if numero_col else "NULL::text AS numero",
            "estado": f"e.{estado_col} AS estado" if estado_col else "NULL::text AS estado",
            "tipo_vehiculo_id": f"e.{tipo_col} AS tipo_vehiculo_id" if tipo_col else "NULL::int AS tipo_vehiculo_id",
            "tipo_vehiculo_nombre": tipo_nombre_expr,
            "fecha_actualizacion": f"e.{fecha_col} AS fecha_actualizacion" if fecha_col else "NULL::timestamp AS fecha_actualizacion",
        }

        query = f"""
            SELECT
                {select_map['id']},
                {select_map['numero']},
                {select_map['estado']},
                {select_map['tipo_vehiculo_id']},
                {select_map['tipo_vehiculo_nombre']},
                {select_map['fecha_actualizacion']}
            FROM public.{table_name} e
            ORDER BY e.{id_col} DESC
        """

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                rows = cur.fetchall()

        return [
            {
                "id": row[0],
                "numero": row[1],
                "estado": row[2],
                "tipo_vehiculo_id": row[3],
                "tipo_vehiculo_nombre": row[4],
                "fecha_actualizacion": row[5],
            }
            for row in rows
        ]

    @classmethod
    def create_item(cls, data: dict) -> None:
        table_name = cls._get_table_name()
        cols = cls._get_columns(table_name)

        field_map = {
            "numero": ["numero", "codigo", "nombre"],
            "estado": ["estado"],
            "tipo_vehiculo_id": ["tipo_vehiculo_id"],
            "fecha_actualizacion": ["fecha_actualizacion", "updated_at"],
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

        id_col = cls._pick_existing(cols, "id_espacio", "id")
        if not id_col:
            raise ValueError(f"La tabla {table_name} no tiene columna identificadora soportada")

        field_map = {
            "numero": ["numero", "codigo", "nombre"],
            "estado": ["estado"],
            "tipo_vehiculo_id": ["tipo_vehiculo_id"],
            "fecha_actualizacion": ["fecha_actualizacion", "updated_at"],
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

    @classmethod
    def get_by_numero(cls, numero: str) -> dict | None:
        table_name = cls._get_table_name()
        cols = cls._get_columns(table_name)

        id_col = cls._pick_existing(cols, "id_espacio", "id")
        numero_col = cls._pick_existing(cols, "numero", "codigo", "nombre")
        estado_col = cls._pick_existing(cols, "estado")
        tipo_col = cls._pick_existing(cols, "tipo_vehiculo_id")
        fecha_col = cls._pick_existing(cols, "fecha_actualizacion", "updated_at")

        if not id_col or not numero_col:
            return None

        query = f"""
            SELECT
                e.{id_col} AS id,
                e.{numero_col} AS numero,
                {f'e.{estado_col}' if estado_col else 'NULL::text'} AS estado,
                {f'e.{tipo_col}' if tipo_col else 'NULL::int'} AS tipo_vehiculo_id,
                {f'e.{fecha_col}' if fecha_col else 'NULL::timestamp'} AS fecha_actualizacion
            FROM public.{table_name} e
            WHERE cast(e.{numero_col} as text) = %s
            LIMIT 1
        """

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (str(numero),))
                row = cur.fetchone()

        if not row:
            return None

        return {
            "id": row[0],
            "numero": row[1],
            "estado": row[2],
            "tipo_vehiculo_id": row[3],
            "fecha_actualizacion": row[4],
        }

    @classmethod
    def get_by_id(cls, item_id: int) -> dict | None:
        table_name = cls._get_table_name()
        cols = cls._get_columns(table_name)

        id_col = cls._pick_existing(cols, "id_espacio", "id")
        numero_col = cls._pick_existing(cols, "numero", "codigo", "nombre")
        estado_col = cls._pick_existing(cols, "estado")
        tipo_col = cls._pick_existing(cols, "tipo_vehiculo_id")
        fecha_col = cls._pick_existing(cols, "fecha_actualizacion", "updated_at")

        if not id_col:
            return None

        query = f"""
            SELECT
                e.{id_col} AS id,
                {f'e.{numero_col}' if numero_col else 'NULL::text'} AS numero,
                {f'e.{estado_col}' if estado_col else 'NULL::text'} AS estado,
                {f'e.{tipo_col}' if tipo_col else 'NULL::int'} AS tipo_vehiculo_id,
                {f'(SELECT tv.nombre FROM public.tipo_vehiculo tv WHERE tv.id = e.{tipo_col} LIMIT 1)' if tipo_col else 'NULL::text'} AS tipo_vehiculo_nombre,
                {f'e.{fecha_col}' if fecha_col else 'NULL::timestamp'} AS fecha_actualizacion
            FROM public.{table_name} e
            WHERE e.{id_col} = %s
            LIMIT 1
        """

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (item_id,))
                row = cur.fetchone()

        if not row:
            return None

        return {
            "id": row[0],
            "numero": row[1],
            "estado": row[2],
            "tipo_vehiculo_id": row[3],
            "tipo_vehiculo_nombre": row[4],
            "fecha_actualizacion": row[5],
        }

    @classmethod
    def upsert_by_numero(cls, data: dict) -> None:
        numero = str(data.get("numero") or "").strip()
        if not numero:
            raise ValueError("El número del espacio es obligatorio")

        existing = cls.get_by_numero(numero)
        if existing:
            cls.update_item(int(existing["id"]), data)
            return

        cls.create_item(data)

    @classmethod
    def delete_item(cls, item_id: int) -> None:
        table_name = cls._get_table_name()
        cols = cls._get_columns(table_name)
        id_col = cls._pick_existing(cols, "id_espacio", "id")
        if not id_col:
            raise ValueError(f"La tabla {table_name} no tiene columna identificadora soportada")

        query = sql.SQL("DELETE FROM public.{table} WHERE {id_col} = %s").format(
            table=sql.Identifier(table_name),
            id_col=sql.Identifier(id_col),
        )

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (item_id,))
            conn.commit()

    @staticmethod
    def _normalize_estado(estado: str | None) -> tuple[str, str]:
        raw = (estado or "").strip().lower()
        if raw in {"ocupado", "ocupa", "occupied"}:
            return "ocupado", "Ocupado"
        if raw in {"inhabilitado", "inactivo", "bloqueado", "disabled", "no_disponible", "fuera_servicio"}:
            return "inhabilitado", "Inhabilitado"
        return "disponible", "Disponible"

    @classmethod
    def build_slots(cls, total_slots: int = 50) -> list[dict]:
        items = cls.list_items()
        mapped: dict[int, dict] = {}

        for item in items:
            try:
                numero_int = int(str(item.get("numero") or "").strip())
            except Exception:
                continue
            if 1 <= numero_int <= total_slots and numero_int not in mapped:
                mapped[numero_int] = item

        slots = []
        for num in range(1, total_slots + 1):
            item = mapped.get(num)
            status_key, status_label = cls._normalize_estado(item.get("estado") if item else "disponible")
            slots.append(
                {
                    "id": item.get("id") if item else None,
                    "numero": num,
                    "estado": status_key,
                    "estado_label": status_label,
                    "tipo_vehiculo_id": item.get("tipo_vehiculo_id") if item else None,
                }
            )

        return slots

    @staticmethod
    def slot_summary(slots: list[dict]) -> dict:
        summary = {"total": len(slots), "disponible": 0, "ocupado": 0, "inhabilitado": 0}
        for slot in slots:
            key = slot.get("estado")
            if key in summary:
                summary[key] += 1
        return summary

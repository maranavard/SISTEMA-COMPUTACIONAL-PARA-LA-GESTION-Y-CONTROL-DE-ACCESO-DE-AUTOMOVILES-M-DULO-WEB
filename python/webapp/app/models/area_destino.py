"""Catalogo administrable de areas destino para visitantes."""

from __future__ import annotations

from app.db import get_connection


class AreaDestino:
    DEFAULT_AREAS = [
        "Administrativa",
        "Bienestar",
        "Sistemas",
        "Cafetería",
        "Biblioteca",
    ]

    @classmethod
    def _ensure_table(cls) -> None:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS public.config_areas_destino (
                        id SERIAL PRIMARY KEY,
                        nombre VARCHAR(80) NOT NULL UNIQUE,
                        activo BOOLEAN NOT NULL DEFAULT TRUE,
                        created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                        updated_at TIMESTAMP NOT NULL DEFAULT NOW()
                    )
                    """
                )

                for area in cls.DEFAULT_AREAS:
                    cur.execute(
                        """
                        INSERT INTO public.config_areas_destino (nombre)
                        VALUES (%s)
                        ON CONFLICT (nombre) DO NOTHING
                        """,
                        (area,),
                    )
            conn.commit()

    @staticmethod
    def _normalize_name(nombre: str) -> str:
        value = (nombre or "").strip()
        if not value:
            raise ValueError("El nombre del area es obligatorio.")
        if len(value) > 80:
            raise ValueError("El nombre del area no puede superar 80 caracteres.")
        return value

    @classmethod
    def list_items(cls, include_inactive: bool = False) -> list[dict]:
        cls._ensure_table()

        where_clause = "" if include_inactive else "WHERE activo = TRUE"
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT id, nombre, activo
                    FROM public.config_areas_destino
                    {where_clause}
                    ORDER BY nombre ASC
                    """
                )
                rows = cur.fetchall()

        return [
            {
                "id": row[0],
                "nombre": row[1],
                "activo": bool(row[2]),
            }
            for row in rows
        ]

    @classmethod
    def list_names(cls) -> list[str]:
        return [item["nombre"] for item in cls.list_items(include_inactive=False)]

    @classmethod
    def create_area(cls, nombre: str) -> None:
        cls._ensure_table()
        nombre_normalizado = cls._normalize_name(nombre)

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO public.config_areas_destino (nombre, activo, updated_at)
                    VALUES (%s, TRUE, NOW())
                    """,
                    (nombre_normalizado,),
                )
            conn.commit()

    @classmethod
    def update_area(cls, area_id: int, nombre: str) -> None:
        cls._ensure_table()
        nombre_normalizado = cls._normalize_name(nombre)

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE public.config_areas_destino
                    SET nombre = %s,
                        updated_at = NOW()
                    WHERE id = %s
                    """,
                    (nombre_normalizado, area_id),
                )
                if cur.rowcount == 0:
                    raise ValueError("No se encontro el area a actualizar.")
            conn.commit()

    @classmethod
    def delete_area(cls, area_id: int) -> None:
        cls._ensure_table()

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    DELETE FROM public.config_areas_destino
                    WHERE id = %s
                    """,
                    (area_id,),
                )
                if cur.rowcount == 0:
                    raise ValueError("No se encontro el area a eliminar.")
            conn.commit()

    @classmethod
    def exists_active(cls, nombre: str) -> bool:
        cls._ensure_table()
        value = (nombre or "").strip()
        if not value:
            return False

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT 1
                    FROM public.config_areas_destino
                    WHERE lower(nombre) = lower(%s)
                      AND activo = TRUE
                    LIMIT 1
                    """,
                    (value,),
                )
                return cur.fetchone() is not None

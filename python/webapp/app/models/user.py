"""Modelo de usuario para autenticación.

Este modelo conecta Flask-Login con la tabla usuarios de PostgreSQL.
"""

from dataclasses import dataclass
from psycopg2 import sql
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app.db import get_connection


@dataclass
class User(UserMixin):
    # Atributos mínimos que usa Flask-Login y la UI actual.
    id: int
    username: str
    password: str
    rol: str

    @staticmethod
    def _normalize_role(role_value) -> str:
        """Normaliza rol en texto simple, incluso si viene serializado como array."""
        role_text = (role_value or "sin_rol")
        if not isinstance(role_text, str):
            role_text = str(role_text)

        role_text = role_text.strip()
        if role_text.startswith("{") and role_text.endswith("}"):
            items = [item.strip().strip('"') for item in role_text[1:-1].split(",") if item.strip()]
            role_text = items[0] if items else "sin_rol"
        if role_text.startswith("[") and role_text.endswith("]"):
            items = [item.strip().strip('"') for item in role_text[1:-1].split(",") if item.strip()]
            role_text = items[0] if items else "sin_rol"

        aliases = {
            "vigilante/seguridad": "seguridad_udec",
            "vigilante_seguridad": "seguridad_udec",
            "seguridad": "seguridad_udec",
            "funcionario": "funcionario_area",
            "funcionario_udec": "funcionario_area",
            "estudiante": "estudiante_udec",
            "alumno": "estudiante_udec",
            "profesor": "docente_udec",
            "docente": "docente_udec",
            "maestro": "docente_udec",
            "conductor": "conductor_udec",
            "visitante": "visitante_udec",
        }
        role_text = aliases.get(role_text, role_text)
        return role_text or "sin_rol"

    @staticmethod
    def _get_table_columns(table_name: str) -> dict[str, str]:
        """Retorna columnas y tipos de una tabla del schema public."""
        query = """
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = %s
        """
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (table_name,))
                return {row[0]: row[1] for row in cur.fetchall()}

    @classmethod
    def _get_usuarios_columns(cls) -> dict[str, str]:
        """Consulta columnas reales de public.usuarios para compatibilidad de esquema."""
        return cls._get_table_columns("usuarios")

    @classmethod
    def _get_roles_columns(cls) -> dict[str, str]:
        """Consulta columnas reales de public.roles para compatibilidad de esquema."""
        return cls._get_table_columns("roles")

    @staticmethod
    def _role_select_expr(user_columns: dict[str, str], role_columns: dict[str, str]) -> tuple[str, str]:
        """Define expresión SQL de rol y JOIN requerido para roles."""
        has_role = "role" in user_columns
        user_fk_col = "rol_id" if "rol_id" in user_columns else ("idrol" if "idrol" in user_columns else None)
        role_pk_col = "id" if "id" in role_columns else ("idrol" if "idrol" in role_columns else None)

        role_name_col = None
        for candidate in ("codigo", "name", "nombre", "rol"):
            if candidate in role_columns:
                role_name_col = candidate
                break

        can_join = bool(user_fk_col and role_pk_col and role_name_col)
        join_sql = (
            f" LEFT JOIN public.roles r ON r.{role_pk_col} = u.{user_fk_col} "
            if can_join
            else ""
        )

        if has_role:
            if can_join:
                return (
                    f"COALESCE(NULLIF(u.role::text, ''), COALESCE(r.{role_name_col}::text, 'sin_rol'), 'sin_rol') AS rol",
                    join_sql,
                )
            return ("COALESCE(NULLIF(u.role::text, ''), 'sin_rol') AS rol", join_sql)

        if can_join:
            return (f"COALESCE(r.{role_name_col}::text, 'sin_rol') AS rol", join_sql)

        return ("'sin_rol' AS rol", join_sql)

    @staticmethod
    def _pick_existing(columns: dict[str, str], *candidates: str) -> str | None:
        for candidate in candidates:
            if candidate in columns:
                return candidate
        return None

    @classmethod
    def _base_select_query(cls, where_clause: str) -> tuple[str, set[str]]:
        """Arma query base para obtener usuario autenticable según esquema disponible."""
        columns = cls._get_usuarios_columns()
        roles_columns = cls._get_roles_columns()
        role_expr, join_roles_sql = cls._role_select_expr(columns, roles_columns)

        query = f"""
            SELECT
                u.id,
                u.username,
                u.password,
                {role_expr}
            FROM public.usuarios u
        """

        query += join_roles_sql

        query += f" {where_clause} LIMIT 1 "
        return query, columns

    @staticmethod
    def _map_row(row):
        # Convierte una fila SQL en objeto User del dominio.
        if not row:
            return None
        return User(
            id=row[0],
            username=row[1],
            password=row[2],
            rol=User._normalize_role(row[3]),
        )

    @classmethod
    def get_by_id(cls, user_id: int):
        # Busca usuario por ID de sesión.
        query, _ = cls._base_select_query("WHERE u.id = %s")
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (user_id,))
                row = cur.fetchone()
        return cls._map_row(row)

    @classmethod
    def get_by_username(cls, username: str):
        # Busca usuario para proceso de login.
        query, _ = cls._base_select_query("WHERE u.username = %s")
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (username,))
                row = cur.fetchone()
        return cls._map_row(row)

    @classmethod
    def get_by_email(cls, email: str):
        # Busca usuario por correo para recuperación de contraseña.
        columns = cls._get_usuarios_columns()
        email_col = cls._pick_existing(columns, "email", "correo", "correo_institucional")
        if not email_col:
            return None

        query, _ = cls._base_select_query(f"WHERE lower(u.{email_col}) = lower(%s)")
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (email,))
                row = cur.fetchone()
        return cls._map_row(row)

    @classmethod
    def list_users(cls) -> list[dict]:
        """Lista usuarios para módulo administrativo."""
        columns = cls._get_usuarios_columns()
        role_columns = cls._get_roles_columns()
        select_fields = ["u.id", "u.username"]

        nombre_col = cls._pick_existing(columns, "nombre", "nombres")
        apellido_col = cls._pick_existing(columns, "apellido", "apellidos")
        email_col = cls._pick_existing(columns, "email", "correo", "correo_institucional")
        id_doc_col = cls._pick_existing(columns, "numero_identificacion", "identificacion", "documento")

        select_fields.append(f"u.{nombre_col} AS nombre" if nombre_col else "NULL::text AS nombre")
        select_fields.append(f"u.{apellido_col} AS apellido" if apellido_col else "NULL::text AS apellido")
        select_fields.append(f"u.{email_col} AS email" if email_col else "NULL::text AS email")
        select_fields.append(
            f"u.{id_doc_col} AS numero_identificacion" if id_doc_col else "NULL::text AS numero_identificacion"
        )

        if "estado" in columns.keys():
            select_fields.append("u.estado")
        else:
            select_fields.append("'activo'::text AS estado")

        role_expr, join_roles_sql = cls._role_select_expr(columns, role_columns)
        select_fields.append(role_expr)

        query = f"SELECT {', '.join(select_fields)} FROM public.usuarios u"
        query += join_roles_sql
        query += " ORDER BY u.id DESC"

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                rows = cur.fetchall()

        return [
            {
                "id": row[0],
                "username": row[1],
                "nombre": row[2],
                "apellido": row[3],
                "email": row[4],
                "numero_identificacion": row[5],
                "estado": row[6],
                "rol": cls._normalize_role(row[7]),
            }
            for row in rows
        ]

    @classmethod
    def create_user(
        cls,
        username: str,
        raw_password: str,
        role: str,
        estado: str,
        nombre: str = "",
        apellido: str = "",
        email: str = "",
        numero_identificacion: str = "",
    ) -> None:
        """Crea usuario nuevo según columnas disponibles."""
        columns = cls._get_usuarios_columns()
        insert_columns = ["username", "password"]
        insert_values = [username, generate_password_hash(raw_password)]
        role_is_array = columns.get("role") == "ARRAY"
        nombre_col = cls._pick_existing(columns, "nombre", "nombres")
        apellido_col = cls._pick_existing(columns, "apellido", "apellidos")
        email_col = cls._pick_existing(columns, "email", "correo", "correo_institucional")
        id_doc_col = cls._pick_existing(columns, "numero_identificacion", "identificacion", "documento")

        if "role" in columns.keys():
            insert_columns.append("role")
            insert_values.append([role] if role_is_array else role)
        if "estado" in columns.keys():
            insert_columns.append("estado")
            insert_values.append(estado)
        if nombre_col:
            insert_columns.append(nombre_col)
            insert_values.append(nombre)
        if apellido_col:
            insert_columns.append(apellido_col)
            insert_values.append(apellido)
        if email_col:
            insert_columns.append(email_col)
            insert_values.append(email)
        if id_doc_col:
            insert_columns.append(id_doc_col)
            insert_values.append(numero_identificacion)

        query = sql.SQL("INSERT INTO public.usuarios ({fields}) VALUES ({vals})").format(
            fields=sql.SQL(", ").join(sql.Identifier(column) for column in insert_columns),
            vals=sql.SQL(", ").join(sql.Placeholder() for _ in insert_columns),
        )

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, insert_values)
            conn.commit()

    @classmethod
    def update_user(
        cls,
        user_id: int,
        role: str,
        estado: str,
        nombre: str = "",
        apellido: str = "",
        email: str = "",
        numero_identificacion: str = "",
    ) -> None:
        """Actualiza datos administrables del usuario."""
        columns = cls._get_usuarios_columns()
        role_is_array = columns.get("role") == "ARRAY"
        nombre_col = cls._pick_existing(columns, "nombre", "nombres")
        apellido_col = cls._pick_existing(columns, "apellido", "apellidos")
        email_col = cls._pick_existing(columns, "email", "correo", "correo_institucional")
        id_doc_col = cls._pick_existing(columns, "numero_identificacion", "identificacion", "documento")
        assignments = []
        values = []

        if "role" in columns.keys():
            assignments.append(sql.SQL("role = {} ").format(sql.Placeholder()))
            values.append([role] if role_is_array else role)
        if "estado" in columns.keys():
            assignments.append(sql.SQL("estado = {} ").format(sql.Placeholder()))
            values.append(estado)
        if nombre_col:
            assignments.append(sql.SQL("{} = {} ").format(sql.Identifier(nombre_col), sql.Placeholder()))
            values.append(nombre)
        if apellido_col:
            assignments.append(sql.SQL("{} = {} ").format(sql.Identifier(apellido_col), sql.Placeholder()))
            values.append(apellido)
        if email_col:
            assignments.append(sql.SQL("{} = {} ").format(sql.Identifier(email_col), sql.Placeholder()))
            values.append(email)
        if id_doc_col:
            assignments.append(sql.SQL("{} = {} ").format(sql.Identifier(id_doc_col), sql.Placeholder()))
            values.append(numero_identificacion)

        if not assignments:
            return

        values.append(user_id)
        query = sql.SQL("UPDATE public.usuarios SET {assignments} WHERE id = %s").format(
            assignments=sql.SQL(", ").join(assignments)
        )

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, values)
            conn.commit()

    @classmethod
    def update_password(cls, user_id: int, raw_password: str) -> None:
        """Actualiza contraseña del usuario usando hash seguro."""
        password_hash = generate_password_hash(raw_password)
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE public.usuarios SET password = %s WHERE id = %s", (password_hash, user_id))
            conn.commit()

    def verify_password(self, candidate_password: str) -> bool:
        # Soporta hash seguro (pbkdf2/scrypt) y fallback temporal en texto plano.
        # Recomendación: migrar todo a hash y eliminar fallback plano.
        if not self.password:
            return False

        try:
            if self.password.startswith(("pbkdf2:", "scrypt:")):
                return check_password_hash(self.password, candidate_password)
        except ValueError:
            return False

        return self.password == candidate_password

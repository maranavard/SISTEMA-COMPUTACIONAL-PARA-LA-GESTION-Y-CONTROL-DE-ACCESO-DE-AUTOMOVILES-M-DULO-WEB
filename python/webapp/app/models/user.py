from dataclasses import dataclass
from flask_login import UserMixin
from werkzeug.security import check_password_hash

from app.db import get_connection


@dataclass
class User(UserMixin):
    id: int
    username: str
    password: str
    rol: str

    @staticmethod
    def _map_row(row):
        if not row:
            return None
        return User(
            id=row[0],
            username=row[1],
            password=row[2],
            rol=row[3] or "sin_rol",
        )

    @classmethod
    def get_by_id(cls, user_id: int):
        sql = """
            SELECT
                u.id,
                u.username,
                u.password,
                COALESCE(
                    NULLIF(u.role, ''),
                    r.codigo,
                    'sin_rol'
                ) AS rol
            FROM public.usuarios u
            LEFT JOIN public.roles r ON r.id = u.rol_id
            WHERE u.id = %s
            LIMIT 1
        """
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (user_id,))
                row = cur.fetchone()
        return cls._map_row(row)

    @classmethod
    def get_by_username(cls, username: str):
        sql = """
            SELECT
                u.id,
                u.username,
                u.password,
                COALESCE(
                    NULLIF(u.role, ''),
                    r.codigo,
                    'sin_rol'
                ) AS rol
            FROM public.usuarios u
            LEFT JOIN public.roles r ON r.id = u.rol_id
            WHERE u.username = %s
            LIMIT 1
        """
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (username,))
                row = cur.fetchone()
        return cls._map_row(row)

    def verify_password(self, candidate_password: str) -> bool:
        if not self.password:
            return False

        try:
            if self.password.startswith(("pbkdf2:", "scrypt:")):
                return check_password_hash(self.password, candidate_password)
        except ValueError:
            return False

        return self.password == candidate_password

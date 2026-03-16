"""Helpers de autorización por rol."""

from functools import wraps
from flask import abort
from flask_login import current_user


def normalize_role(role_value) -> str:
    role_text = (role_value or "")
    if not isinstance(role_text, str):
        role_text = str(role_text)

    role_text = role_text.strip().lower()
    if role_text.startswith("{") and role_text.endswith("}"):
        parts = [item.strip().strip('"') for item in role_text[1:-1].split(",") if item.strip()]
        return parts[0] if parts else ""
    if role_text.startswith("[") and role_text.endswith("]"):
        parts = [item.strip().strip('"') for item in role_text[1:-1].split(",") if item.strip()]
        return parts[0] if parts else ""
    return role_text


def roles_required(allowed_roles: set[str]):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)

            rol = normalize_role(getattr(current_user, "rol", ""))
            if rol not in allowed_roles:
                abort(403)

            return view_func(*args, **kwargs)

        return wrapper

    return decorator


def admin_required(view_func):
    """Permite acceso solo a perfiles administrativos."""
    allowed = {"admin_sistema", "admin", "administrador"}
    return roles_required(allowed)(view_func)


def community_required(view_func):
    """Permite acceso a comunidad UDEC y perfiles administrativos."""
    allowed = {
        "admin_sistema",
        "admin",
        "administrador",
        "seguridad_udec",
        "vigilante",
        "vigilancia",
        "conductor_udec",
        "estudiante_udec",
        "estudiante",
        "alumno",
        "usuario",
        "visitante",
        "visitante_udec",
        "funcionario_area",
        "funcionario",
        "funcionario_udec",
    }
    return roles_required(allowed)(view_func)

"""Helpers de autorización por rol."""

from functools import wraps
from flask import abort
from flask_login import current_user


def admin_required(view_func):
    """Permite acceso solo a perfiles administrativos."""

    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(401)

        rol_raw = (getattr(current_user, "rol", "") or "").strip().lower()

        # Soporta rol simple ('admin_sistema') o serialización de arreglo ('{admin_sistema}').
        rol = rol_raw
        if rol.startswith("{") and rol.endswith("}"):
            parts = [item.strip().strip('"') for item in rol[1:-1].split(",") if item.strip()]
            rol = parts[0] if parts else ""
        elif rol.startswith("[") and rol.endswith("]"):
            parts = [item.strip().strip('"') for item in rol[1:-1].split(",") if item.strip()]
            rol = parts[0] if parts else ""

        allowed = {"admin_sistema", "admin", "administrador"}
        if rol not in allowed:
            abort(403)

        return view_func(*args, **kwargs)

    return wrapper

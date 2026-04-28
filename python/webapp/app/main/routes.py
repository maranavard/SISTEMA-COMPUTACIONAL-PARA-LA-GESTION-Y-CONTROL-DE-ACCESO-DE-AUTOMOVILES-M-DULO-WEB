"""Rutas principales del módulo web.

Incluye entrada del sitio y panel protegido.
"""

from flask import Blueprint, redirect, render_template, url_for
from flask_login import current_user, login_required

from app.utils.authz import normalize_role


main_bp = Blueprint("main", __name__)


@main_bp.get("/")
def index():
    # Redirige al panel si hay sesión, o a login si no hay sesión.
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    return redirect(url_for("auth.login"))


@main_bp.get("/dashboard")
@login_required
def dashboard():
    # Ruta protegida: requiere sesión activa.
    rol = normalize_role(getattr(current_user, "rol", ""))
    panel_admin_roles = {"admin_sistema", "admin", "administrador"}
    panel_vigilante_roles = {"seguridad_udec", "vigilante", "vigilancia"}
    if rol in panel_admin_roles:
        panel_type = "admin"
    elif rol in panel_vigilante_roles:
        panel_type = "vigilante"
    else:
        panel_type = "general"
    return render_template("dashboard.html", user=current_user, panel_type=panel_type, current_role=rol)


@main_bp.get("/mi-cuenta")
@login_required
def mi_cuenta():
    return render_template("main/mi_cuenta.html", user=current_user)

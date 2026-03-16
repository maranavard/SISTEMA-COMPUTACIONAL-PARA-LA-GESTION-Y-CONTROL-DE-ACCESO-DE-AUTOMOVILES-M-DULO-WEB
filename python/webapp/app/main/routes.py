"""Rutas principales del módulo web.

Incluye entrada del sitio y panel protegido.
"""

from flask import Blueprint, redirect, render_template, url_for
from flask_login import current_user, login_required


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
    rol = (getattr(current_user, "rol", "") or "").strip().lower()
    panel_admin_roles = {"admin_sistema", "admin", "administrador", "seguridad_udec", "vigilante", "vigilancia"}
    panel_type = "admin" if rol in panel_admin_roles else "general"
    return render_template("dashboard.html", user=current_user, panel_type=panel_type)

"""Rutas principales del módulo web.

Incluye entrada del sitio y panel protegido.
"""

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.models.user import User
from app.utils.authz import normalize_role
from app.utils.field_validators import (
    is_valid_cedula,
    is_valid_email,
    normalize_cedula,
    normalize_email,
)


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


@main_bp.post("/mi-cuenta/actualizar")
@login_required
def actualizar_mi_cuenta():
    nombre = request.form.get("nombre", "").strip()
    apellido = request.form.get("apellido", "").strip()
    email = normalize_email(request.form.get("email", ""))
    numero_identificacion = normalize_cedula(request.form.get("numero_identificacion", ""))
    new_password = request.form.get("new_password", "").strip()

    if email and not is_valid_email(email):
        flash("Formato de correo inválido. Usa un correo válido (ej: usuario@dominio.com).", "error")
        return redirect(url_for("main.mi_cuenta"))

    if numero_identificacion and not is_valid_cedula(numero_identificacion):
        flash("Formato de cédula inválido. Debe contener solo números (6 a 12 dígitos).", "error")
        return redirect(url_for("main.mi_cuenta"))

    try:
        User.update_user(
            user_id=int(current_user.id),
            role=getattr(current_user, "rol", ""),
            estado=getattr(current_user, "estado", "activo"),
            nombre=nombre,
            apellido=apellido,
            email=email,
            numero_identificacion=numero_identificacion,
        )

        if new_password:
            User.update_password(user_id=int(current_user.id), raw_password=new_password)

        flash("Tus datos fueron actualizados correctamente.", "success")
    except Exception as exc:
        flash(f"No se pudo actualizar tu cuenta: {exc}", "error")

    return redirect(url_for("main.mi_cuenta"))

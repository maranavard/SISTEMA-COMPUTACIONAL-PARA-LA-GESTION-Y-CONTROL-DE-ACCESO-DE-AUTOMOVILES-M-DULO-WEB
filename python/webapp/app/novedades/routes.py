"""Módulo de novedades: ingreso/salida por placa y consulta histórica."""

from functools import wraps

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.models.novedad import Novedad


novedades_bp = Blueprint("novedades", __name__, url_prefix="/novedades")


def control_access_required(view_func):
    """Permite acceso a roles de administración y seguridad/control."""

    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(401)

        rol_raw = (getattr(current_user, "rol", "") or "").strip().lower()
        rol = rol_raw

        if rol.startswith("{") and rol.endswith("}"):
            parts = [item.strip().strip('"') for item in rol[1:-1].split(",") if item.strip()]
            rol = parts[0] if parts else ""
        elif rol.startswith("[") and rol.endswith("]"):
            parts = [item.strip().strip('"') for item in rol[1:-1].split(",") if item.strip()]
            rol = parts[0] if parts else ""

        allowed = {"admin_sistema", "admin", "administrador", "seguridad_udec", "vigilante", "vigilancia"}
        if rol not in allowed:
            abort(403)

        return view_func(*args, **kwargs)

    return wrapper


@novedades_bp.get("/")
@login_required
@control_access_required
def index():
    return render_template("novedades/index.html")


@novedades_bp.post("/registrar")
@login_required
@control_access_required
def registrar_novedad():
    placa = (request.form.get("placa", "") or "").strip().upper()
    payload = {
        "tipo_novedad": (request.form.get("tipo_novedad", "") or "").strip().lower() or "novedad",
        "placa": placa,
        "fecha_hora": (request.form.get("fecha_hora", "") or "").strip(),
        "observaciones": (request.form.get("observaciones", "") or "").strip(),
        "estado": (request.form.get("estado", "") or "").strip() or "registrado",
        "id_usuario": int(current_user.id),
    }

    if not placa:
        flash("Debes indicar la placa del vehículo para registrar la novedad.", "error")
        return redirect(url_for("novedades.index"))

    try:
        novedad_id = Novedad.create_reporte(payload)
        flash(f"Novedad registrada correctamente. ID: {novedad_id}", "success")
    except Exception as exc:
        flash(f"No se pudo registrar la novedad: {exc}", "error")
        return redirect(url_for("novedades.index"))

    return redirect(url_for("novedades.gestion"))


@novedades_bp.get("/gestion")
@login_required
@control_access_required
def gestion():
    items = Novedad.list_recent(limit=120)
    return render_template("novedades/gestion.html", items=items)

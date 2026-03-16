"""Rutas del módulo Consulta por Placa."""

from functools import wraps

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.models.vehiculo import Vehiculo


consultas_bp = Blueprint("consultas", __name__, url_prefix="/consultas")


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


@consultas_bp.get("/")
@login_required
@control_access_required
def index():
    placa_filtro = (request.args.get("placa", "") or "").strip().upper()
    items = Vehiculo.list_items()

    if placa_filtro:
        items = [item for item in items if (item.get("placa") or "").upper().find(placa_filtro) >= 0]

    return render_template("consultas/index.html", items=items, placa_filtro=placa_filtro)


@consultas_bp.get("/<int:item_id>")
@login_required
@control_access_required
def visualizar(item_id: int):
    item = Vehiculo.get_by_id(item_id)
    if not item:
        flash("No se encontró el vehículo solicitado.", "error")
        return redirect(url_for("consultas.index"))

    return render_template("consultas/view.html", item=item)


@consultas_bp.get("/<int:item_id>/editar")
@login_required
@control_access_required
def editar(item_id: int):
    item = Vehiculo.get_by_id(item_id)
    if not item:
        flash("No se encontró el vehículo para editar.", "error")
        return redirect(url_for("consultas.index"))

    return render_template("consultas/edit.html", item=item)


@consultas_bp.post("/<int:item_id>/editar")
@login_required
@control_access_required
def guardar_edicion(item_id: int):
    payload = {
        "placa": (request.form.get("placa", "") or "").strip().upper(),
        "marca": (request.form.get("marca", "") or "").strip(),
        "modelo": (request.form.get("modelo", "") or "").strip(),
        "color": (request.form.get("color", "") or "").strip(),
        "tipo_vehiculo_id": (request.form.get("tipo_vehiculo_id", "") or "").strip(),
        "estado": (request.form.get("estado", "") or "").strip(),
    }

    try:
        Vehiculo.update_item(item_id=item_id, data=payload)
        flash("Vehículo actualizado correctamente.", "success")
    except Exception as exc:
        flash(f"No se pudo actualizar el vehículo: {exc}", "error")

    return redirect(url_for("consultas.index"))


@consultas_bp.post("/<int:item_id>/borrar")
@login_required
@control_access_required
def borrar(item_id: int):
    try:
        Vehiculo.delete_item(item_id)
        flash("Vehículo eliminado correctamente.", "success")
    except Exception as exc:
        flash(f"No se pudo eliminar el vehículo: {exc}", "error")

    return redirect(url_for("consultas.index"))

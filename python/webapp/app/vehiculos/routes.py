"""CRUD de vehiculos (Sprint 1)."""

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required

from app.models.vehiculo import Vehiculo
from app.utils.authz import community_required


vehiculos_bp = Blueprint("vehiculos", __name__, url_prefix="/vehiculos")


@vehiculos_bp.get("/")
@login_required
@community_required
def list_items():
    placa_consulta = (request.args.get("placa", "") or "").strip().upper()
    vehiculo_consulta = None
    if placa_consulta:
        vehiculo_consulta = Vehiculo.get_by_placa(placa_consulta)
    return render_template("vehiculos/index.html", placa_consulta=placa_consulta, vehiculo_consulta=vehiculo_consulta)


@vehiculos_bp.post("/crear")
@login_required
@community_required
def create_item():
    payload = {
        "placa": request.form.get("placa", "").strip().upper(),
        "tipo_vehiculo_id": request.form.get("tipo_vehiculo_id", "").strip(),
        "marca": request.form.get("marca", "").strip(),
        "modelo": request.form.get("modelo", "").strip(),
        "color": request.form.get("color", "").strip(),
        "fecha_registro": request.form.get("fecha_registro", "").strip(),
        "estado": request.form.get("estado", "").strip(),
        "conductor_id": request.form.get("conductor_id", "").strip(),
        "user_id": request.form.get("user_id", "").strip(),
    }

    try:
        Vehiculo.create_item(payload)
        flash("Vehiculo creado correctamente.", "success")
    except Exception as exc:
        flash(f"No se pudo crear vehiculo: {exc}", "error")

    return redirect(url_for("vehiculos.list_items"))


@vehiculos_bp.get("/consultar")
@login_required
@community_required
def consultar_por_placa():
    placa = (request.args.get("placa", "") or "").strip().upper()
    if not placa:
        return redirect(url_for("vehiculos.list_items"))
    return redirect(url_for("vehiculos.list_items", placa=placa))


@vehiculos_bp.post("/<int:item_id>/actualizar")
@login_required
@community_required
def update_item(item_id: int):
    payload = {
        "placa": request.form.get("placa", "").strip().upper(),
        "tipo_vehiculo_id": request.form.get("tipo_vehiculo_id", "").strip(),
        "marca": request.form.get("marca", "").strip(),
        "modelo": request.form.get("modelo", "").strip(),
        "color": request.form.get("color", "").strip(),
        "estado": request.form.get("estado", "").strip(),
        "conductor_id": request.form.get("conductor_id", "").strip(),
        "user_id": request.form.get("user_id", "").strip(),
    }

    try:
        Vehiculo.update_item(item_id=item_id, data=payload)
        flash("Vehiculo actualizado correctamente.", "success")
    except Exception as exc:
        flash(f"No se pudo actualizar vehiculo: {exc}", "error")

    return redirect(url_for("vehiculos.list_items"))

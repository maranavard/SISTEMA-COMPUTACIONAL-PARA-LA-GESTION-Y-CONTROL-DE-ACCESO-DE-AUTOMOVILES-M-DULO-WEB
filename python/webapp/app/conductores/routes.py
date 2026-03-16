"""CRUD de conductores (Sprint 1)."""

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required

from app.models.conductor import Conductor
from app.utils.authz import admin_required


conductores_bp = Blueprint("conductores", __name__, url_prefix="/conductores")


@conductores_bp.get("/")
@login_required
@admin_required
def list_items():
    items = Conductor.list_items()
    return render_template("conductores/index.html", items=items)


@conductores_bp.post("/crear")
@login_required
@admin_required
def create_item():
    payload = {
        "nombre": request.form.get("nombre", "").strip(),
        "apellido": request.form.get("apellido", "").strip(),
        "cedula": request.form.get("cedula", "").strip(),
        "email": request.form.get("email", "").strip(),
        "telefono": request.form.get("telefono", "").strip(),
        "dependencia": request.form.get("dependencia", "").strip(),
        "tipo": request.form.get("tipo", "").strip(),
        "estado": request.form.get("estado", "activo").strip() or "activo",
        "numero_pase": request.form.get("numero_pase", "").strip(),
        "categoria_pase": request.form.get("categoria_pase", "").strip(),
        "fecha_registro": request.form.get("fecha_registro", "").strip(),
        "fecha_vencimiento_pase": request.form.get("fecha_vencimiento_pase", "").strip(),
    }

    try:
        Conductor.create_item(payload)
        flash("Conductor creado correctamente.", "success")
    except Exception as exc:
        flash(f"No se pudo crear conductor: {exc}", "error")

    return redirect(url_for("conductores.list_items"))


@conductores_bp.post("/<int:item_id>/actualizar")
@login_required
@admin_required
def update_item(item_id: int):
    payload = {
        "nombre": request.form.get("nombre", "").strip(),
        "apellido": request.form.get("apellido", "").strip(),
        "cedula": request.form.get("cedula", "").strip(),
        "email": request.form.get("email", "").strip(),
        "telefono": request.form.get("telefono", "").strip(),
        "dependencia": request.form.get("dependencia", "").strip(),
        "tipo": request.form.get("tipo", "").strip(),
        "estado": request.form.get("estado", "activo").strip() or "activo",
        "numero_pase": request.form.get("numero_pase", "").strip(),
        "categoria_pase": request.form.get("categoria_pase", "").strip(),
        "fecha_registro": request.form.get("fecha_registro", "").strip(),
        "fecha_vencimiento_pase": request.form.get("fecha_vencimiento_pase", "").strip(),
    }

    try:
        Conductor.update_item(item_id=item_id, data=payload)
        flash("Conductor actualizado correctamente.", "success")
    except Exception as exc:
        flash(f"No se pudo actualizar conductor: {exc}", "error")

    return redirect(url_for("conductores.list_items"))

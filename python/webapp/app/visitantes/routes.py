"""CRUD de visitantes (Sprint 1)."""

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.models.visitante import Visitante
from app.utils.authz import admin_required


visitantes_bp = Blueprint("visitantes", __name__, url_prefix="/visitantes")


@visitantes_bp.get("/")
@login_required
@admin_required
def list_items():
    return render_template("visitantes/index.html")


@visitantes_bp.post("/crear")
@login_required
@admin_required
def create_item():
    payload = {
        "nombres": request.form.get("nombres", "").strip(),
        "apellidos": request.form.get("apellidos", "").strip(),
        "numero_identificacion": request.form.get("numero_identificacion", "").strip(),
        "area_destino": request.form.get("area_destino", "").strip(),
        "motivo_visita": request.form.get("motivo_visita", "").strip(),
        "placa": request.form.get("placa", "").strip().upper(),
        "fecha_hora_registro": request.form.get("fecha_hora_registro", "").strip(),
        "fecha_hora_prevista": request.form.get("fecha_hora_prevista", "").strip(),
        "estado": request.form.get("estado", "pendiente").strip() or "pendiente",
        "registrado_por_usuario_id": str(getattr(current_user, "id", "") or "").strip(),
    }

    try:
        Visitante.create_item(payload)
        flash("Visitante creado correctamente.", "success")
    except Exception as exc:
        flash(f"No se pudo crear visitante: {exc}", "error")

    return redirect(url_for("visitantes.list_items"))


@visitantes_bp.post("/<int:item_id>/actualizar")
@login_required
@admin_required
def update_item(item_id: int):
    payload = {
        "nombres": request.form.get("nombres", "").strip(),
        "apellidos": request.form.get("apellidos", "").strip(),
        "numero_identificacion": request.form.get("numero_identificacion", "").strip(),
        "area_destino": request.form.get("area_destino", "").strip(),
        "motivo_visita": request.form.get("motivo_visita", "").strip(),
        "placa": request.form.get("placa", "").strip().upper(),
        "fecha_hora_prevista": request.form.get("fecha_hora_prevista", "").strip(),
        "estado": request.form.get("estado", "").strip(),
        "registrado_por_usuario_id": request.form.get("registrado_por_usuario_id", "").strip(),
    }

    try:
        Visitante.update_item(item_id=item_id, data=payload)
        flash("Visitante actualizado correctamente.", "success")
    except Exception as exc:
        flash(f"No se pudo actualizar visitante: {exc}", "error")

    return redirect(url_for("visitantes.list_items"))

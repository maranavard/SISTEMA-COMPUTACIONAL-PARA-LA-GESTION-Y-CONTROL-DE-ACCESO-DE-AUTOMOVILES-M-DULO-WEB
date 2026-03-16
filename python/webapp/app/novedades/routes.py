"""Módulo de novedades: ingreso/salida por placa y consulta histórica."""

from datetime import datetime
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.models.novedad import Novedad
from app.utils.authz import community_required


novedades_bp = Blueprint("novedades", __name__, url_prefix="/novedades")


@novedades_bp.get("/")
@login_required
@community_required
def index():
    return render_template("novedades/index.html")


@novedades_bp.post("/registrar")
@login_required
@community_required
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
@community_required
def gestion():
    placa = (request.args.get("placa", "") or "").strip().upper()
    tipo = (request.args.get("tipo", "") or "").strip().lower()
    fecha_desde_raw = (request.args.get("fecha_desde", "") or "").strip()
    fecha_hasta_raw = (request.args.get("fecha_hasta", "") or "").strip()

    items = Novedad.list_recent(limit=300)

    if placa:
        items = [
            item for item in items
            if placa in str(item.get("placa") or "").upper()
        ]

    if tipo:
        items = [
            item for item in items
            if tipo in str(item.get("tipo_novedad") or "").lower()
        ]

    fecha_desde = None
    fecha_hasta = None
    try:
        if fecha_desde_raw:
            fecha_desde = datetime.strptime(fecha_desde_raw, "%Y-%m-%d").date()
        if fecha_hasta_raw:
            fecha_hasta = datetime.strptime(fecha_hasta_raw, "%Y-%m-%d").date()
    except ValueError:
        flash("Formato de fecha inválido en filtros. Usa AAAA-MM-DD.", "error")

    if fecha_desde or fecha_hasta:
        filtered = []
        for item in items:
            fecha_item = item.get("fecha_hora")
            if not fecha_item:
                continue
            fecha_item_date = fecha_item.date() if hasattr(fecha_item, "date") else None
            if not fecha_item_date:
                continue
            if fecha_desde and fecha_item_date < fecha_desde:
                continue
            if fecha_hasta and fecha_item_date > fecha_hasta:
                continue
            filtered.append(item)
        items = filtered

    return render_template(
        "novedades/gestion.html",
        items=items,
        filtros={
            "placa": placa,
            "tipo": tipo,
            "fecha_desde": fecha_desde_raw,
            "fecha_hasta": fecha_hasta_raw,
        },
    )

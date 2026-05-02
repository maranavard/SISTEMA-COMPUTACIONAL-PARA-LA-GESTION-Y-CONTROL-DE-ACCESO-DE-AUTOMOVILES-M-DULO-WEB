"""Módulo de novedades: ingreso/salida por placa y consulta histórica."""

from datetime import datetime
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.models.novedad import Novedad
from app.utils.authz import community_required, normalize_role


novedades_bp = Blueprint("novedades", __name__, url_prefix="/novedades")
INDEX_ROUTE = "novedades.index"
GESTION_ROUTE = "novedades.gestion"


def _redirect_index():
    return redirect(url_for(INDEX_ROUTE))


def _parse_gestion_filters() -> tuple[str, str, str, str]:
    placa = (request.args.get("placa", "") or "").strip().upper()
    tipo = (request.args.get("tipo", "") or "").strip().lower()
    fecha_desde_raw = (request.args.get("fecha_desde", "") or "").strip()
    fecha_hasta_raw = (request.args.get("fecha_hasta", "") or "").strip()
    return placa, tipo, fecha_desde_raw, fecha_hasta_raw


def _parse_date_filters(fecha_desde_raw: str, fecha_hasta_raw: str):
    fecha_desde = None
    fecha_hasta = None
    try:
        if fecha_desde_raw:
            fecha_desde = datetime.strptime(fecha_desde_raw, "%Y-%m-%d").date()
        if fecha_hasta_raw:
            fecha_hasta = datetime.strptime(fecha_hasta_raw, "%Y-%m-%d").date()
    except ValueError:
        flash("Formato de fecha inválido en filtros. Usa AAAA-MM-DD.", "error")
    return fecha_desde, fecha_hasta


def _apply_text_filters(items: list[dict], placa: str, tipo: str) -> list[dict]:
    filtered = items
    if placa:
        filtered = [
            item for item in filtered
            if placa in str(item.get("placa") or "").upper()
        ]

    if tipo:
        filtered = [
            item for item in filtered
            if tipo in str(item.get("tipo_novedad") or "").lower()
        ]

    return filtered


def _apply_date_filters(items: list[dict], fecha_desde, fecha_hasta) -> list[dict]:
    if not (fecha_desde or fecha_hasta):
        return items

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
    return filtered


def _apply_guard_today_filter(items: list[dict]) -> tuple[list[dict], bool]:
    if not _is_guard_role():
        return items, False

    today = datetime.now().date()
    filtered = [
        item for item in items
        if item.get("fecha_hora") and hasattr(item.get("fecha_hora"), "date") and item.get("fecha_hora").date() == today
    ]
    return filtered, True


def _is_guard_role() -> bool:
    rol = normalize_role(getattr(current_user, "rol", ""))
    return rol in {"vigilante", "vigilancia", "seguridad_udec"}


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
        return _redirect_index()

    try:
        novedad_id = Novedad.create_reporte(payload)
        flash(f"Novedad registrada correctamente. ID: {novedad_id}", "success")
    except Exception as exc:
        flash(f"No se pudo registrar la novedad: {exc}", "error")
        return _redirect_index()

    return redirect(url_for(GESTION_ROUTE))


@novedades_bp.get("/gestion")
@login_required
@community_required
def gestion():
    placa, tipo, fecha_desde_raw, fecha_hasta_raw = _parse_gestion_filters()

    items = Novedad.list_recent(limit=300)
    items = _apply_text_filters(items=items, placa=placa, tipo=tipo)

    fecha_desde, fecha_hasta = _parse_date_filters(
        fecha_desde_raw=fecha_desde_raw,
        fecha_hasta_raw=fecha_hasta_raw,
    )
    items = _apply_date_filters(items=items, fecha_desde=fecha_desde, fecha_hasta=fecha_hasta)
    items, guard_today_only = _apply_guard_today_filter(items)

    return render_template(
        "novedades/gestion.html",
        items=items,
        guard_today_only=guard_today_only,
        filtros={
            "placa": placa,
            "tipo": tipo,
            "fecha_desde": fecha_desde_raw,
            "fecha_hasta": fecha_hasta_raw,
        },
    )

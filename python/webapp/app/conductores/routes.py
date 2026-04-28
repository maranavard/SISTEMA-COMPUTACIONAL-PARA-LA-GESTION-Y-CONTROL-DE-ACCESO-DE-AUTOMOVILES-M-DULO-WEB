"""CRUD de conductores (Sprint 1)."""

from datetime import date, datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.models.conductor import Conductor
from app.utils.authz import community_required, normalize_role
from app.utils.field_validators import is_valid_cedula, is_valid_email, normalize_cedula, normalize_email


conductores_bp = Blueprint("conductores", __name__, url_prefix="/conductores")

WARNING_DAYS = 30
SENSITIVE_ALLOWED_ROLES = {"admin_sistema", "admin", "administrador"}


def _can_manage_sensitive() -> bool:
    rol = normalize_role(getattr(current_user, "rol", ""))
    return rol in SENSITIVE_ALLOWED_ROLES


def _parse_date(raw_value):
    if raw_value in (None, ""):
        return None

    if hasattr(raw_value, "date") and hasattr(raw_value, "hour"):
        return raw_value.date()
    if isinstance(raw_value, date):
        return raw_value

    text = str(raw_value).strip()
    if not text:
        return None

    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue

    if len(text) >= 10:
        try:
            return datetime.strptime(text[:10], "%Y-%m-%d").date()
        except ValueError:
            pass

    return None


def _to_datetime_local_input(raw_value) -> str:
    if raw_value in (None, ""):
        return ""
    if hasattr(raw_value, "strftime"):
        return raw_value.strftime("%Y-%m-%dT%H:%M")

    text = str(raw_value).strip()
    if not text:
        return ""

    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(text, fmt).strftime("%Y-%m-%dT%H:%M")
        except ValueError:
            continue
    return text[:16].replace(" ", "T")


def _to_date_input(raw_value) -> str:
    parsed = _parse_date(raw_value)
    return parsed.isoformat() if parsed else ""


def _document_status(fecha_vencimiento_raw) -> dict:
    fecha_vencimiento = _parse_date(fecha_vencimiento_raw)
    if not fecha_vencimiento:
        return {
            "level": "error",
            "label": "Sin fecha",
            "message": "No tiene fecha de vencimiento del pase registrada.",
            "days": None,
        }

    days = (fecha_vencimiento - date.today()).days
    if days < 0:
        return {
            "level": "error",
            "label": "Vencido",
            "message": f"Documento vencido hace {abs(days)} días.",
            "days": days,
        }
    if days <= WARNING_DAYS:
        return {
            "level": "warning",
            "label": "Por vencer",
            "message": f"Documento próximo a vencer en {days} días.",
            "days": days,
        }
    return {
        "level": "success",
        "label": "Vigente",
        "message": "Documento vigente.",
        "days": days,
    }


def _flash_document_alert(fecha_vencimiento_raw) -> None:
    status = _document_status(fecha_vencimiento_raw)
    if status["level"] == "warning":
        flash(status["message"], "warning")
    elif status["level"] == "error":
        flash(status["message"], "error")


def _validate_fecha_vencimiento_pase(raw_value: str) -> tuple[bool, str]:
    value = (raw_value or "").strip()
    if not value:
        return False, "Debes registrar la fecha de vencimiento del pase."

    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        return False, "La fecha de vencimiento del pase no tiene un formato válido."

    return True, ""


@conductores_bp.get("/")
@login_required
@community_required
def list_items():
    can_manage_sensitive = _can_manage_sensitive()
    items = Conductor.list_items()
    cedula_filtro = (request.args.get("cedula", "") or "").strip()
    if cedula_filtro and can_manage_sensitive:
        needle = cedula_filtro.lower()
        items = [
            item
            for item in items
            if needle in str(item.get("cedula") or "").lower()
        ]

    warning_items = []
    error_items = []

    if can_manage_sensitive:
        for item in items:
            status = _document_status(item.get("fecha_vencimiento_pase"))
            item["doc_status_level"] = status["level"]
            item["doc_status_label"] = status["label"]
            item["doc_status_message"] = status["message"]
            item["dias_para_vencer"] = status["days"]
            item["fecha_registro_input"] = _to_datetime_local_input(item.get("fecha_registro"))
            item["fecha_vencimiento_pase_input"] = _to_date_input(item.get("fecha_vencimiento_pase"))

            if status["level"] == "warning":
                warning_items.append(item)
            if status["level"] == "error":
                error_items.append(item)

    return render_template(
        "conductores/index.html",
        items=items,
        cedula_filtro=cedula_filtro,
        warning_items=warning_items,
        error_items=error_items,
        can_manage_sensitive=can_manage_sensitive,
    )


@conductores_bp.post("/crear")
@login_required
@community_required
def create_item():
    if not _can_manage_sensitive():
        flash("No tienes permisos para registrar o editar perfiles de conductor.", "error")
        return redirect(url_for("conductores.list_items"))

    cedula = normalize_cedula(request.form.get("cedula", ""))
    email = normalize_email(request.form.get("email", ""))

    if not is_valid_cedula(cedula):
        flash("Formato de cédula inválido. Debe contener solo números (6 a 12 dígitos).", "error")
        return redirect(url_for("conductores.list_items"))

    if not is_valid_email(email):
        flash("Formato de correo inválido. Usa un correo válido (ej: usuario@dominio.com).", "error")
        return redirect(url_for("conductores.list_items"))

    fecha_vencimiento_pase = request.form.get("fecha_vencimiento_pase", "").strip()
    fecha_ok, fecha_error = _validate_fecha_vencimiento_pase(fecha_vencimiento_pase)
    if not fecha_ok:
        flash(fecha_error, "error")
        return redirect(url_for("conductores.list_items"))

    payload = {
        "nombre": request.form.get("nombre", "").strip(),
        "apellido": request.form.get("apellido", "").strip(),
        "cedula": cedula,
        "email": email,
        "telefono": request.form.get("telefono", "").strip(),
        "dependencia": request.form.get("dependencia", "").strip(),
        "tipo": request.form.get("tipo", "").strip(),
        "estado": request.form.get("estado", "activo").strip() or "activo",
        "numero_pase": request.form.get("numero_pase", "").strip(),
        "categoria_pase": request.form.get("categoria_pase", "").strip(),
        "fecha_registro": request.form.get("fecha_registro", "").strip(),
        "fecha_vencimiento_pase": fecha_vencimiento_pase,
    }

    try:
        Conductor.create_item(payload)
        flash("Conductor creado correctamente.", "success")
        _flash_document_alert(fecha_vencimiento_pase)
    except Exception as exc:
        flash(f"No se pudo crear conductor: {exc}", "error")

    return redirect(url_for("conductores.list_items"))


@conductores_bp.post("/<int:item_id>/actualizar")
@login_required
@community_required
def update_item(item_id: int):
    if not _can_manage_sensitive():
        flash("No tienes permisos para actualizar información documental de otros usuarios.", "error")
        return redirect(url_for("conductores.list_items"))

    cedula = normalize_cedula(request.form.get("cedula", ""))
    email = normalize_email(request.form.get("email", ""))

    if not is_valid_cedula(cedula):
        flash("Formato de cédula inválido. Debe contener solo números (6 a 12 dígitos).", "error")
        return redirect(url_for("conductores.list_items"))

    if not is_valid_email(email):
        flash("Formato de correo inválido. Usa un correo válido (ej: usuario@dominio.com).", "error")
        return redirect(url_for("conductores.list_items"))

    fecha_vencimiento_pase = request.form.get("fecha_vencimiento_pase", "").strip()
    fecha_ok, fecha_error = _validate_fecha_vencimiento_pase(fecha_vencimiento_pase)
    if not fecha_ok:
        flash(fecha_error, "error")
        return redirect(url_for("conductores.list_items"))

    payload = {
        "nombre": request.form.get("nombre", "").strip(),
        "apellido": request.form.get("apellido", "").strip(),
        "cedula": cedula,
        "email": email,
        "telefono": request.form.get("telefono", "").strip(),
        "dependencia": request.form.get("dependencia", "").strip(),
        "tipo": request.form.get("tipo", "").strip(),
        "estado": request.form.get("estado", "activo").strip() or "activo",
        "numero_pase": request.form.get("numero_pase", "").strip(),
        "categoria_pase": request.form.get("categoria_pase", "").strip(),
        "fecha_registro": request.form.get("fecha_registro", "").strip(),
        "fecha_vencimiento_pase": fecha_vencimiento_pase,
    }

    try:
        Conductor.update_item(item_id=item_id, data=payload)
        flash("Conductor actualizado correctamente.", "success")
        _flash_document_alert(fecha_vencimiento_pase)
    except Exception as exc:
        flash(f"No se pudo actualizar conductor: {exc}", "error")

    return redirect(url_for("conductores.list_items"))

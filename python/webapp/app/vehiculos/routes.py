"""CRUD de vehiculos (Sprint 1)."""

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.models.conductor import Conductor
from app.models.documento_vehiculo import DocumentoVehiculo
from app.models.horario import HorarioOperacion
from app.models.user import User
from app.models.vehiculo import Vehiculo
from app.utils.authz import community_required, normalize_role
from app.utils.schedule_alerts import send_admin_offday_alert


vehiculos_bp = Blueprint("vehiculos", __name__, url_prefix="/vehiculos")

WARNING_DAYS = 30
SENSITIVE_ALLOWED_ROLES = {"admin_sistema", "admin", "administrador"}


def _can_manage_sensitive() -> bool:
    rol = normalize_role(getattr(current_user, "rol", ""))
    return rol in SENSITIVE_ALLOWED_ROLES


def _normalize_lookup_text(value: str) -> str:
    return " ".join((value or "").strip().lower().split())


def _resolve_conductor_id(raw_value: str) -> str:
    value = (raw_value or "").strip()
    if not value:
        return ""
    if value.isdigit():
        return value

    needle = _normalize_lookup_text(value)
    for conductor in Conductor.list_items():
        conductor_id = str(conductor.get("id") or "").strip()
        nombre = _normalize_lookup_text(str(conductor.get("nombre") or ""))
        apellido = _normalize_lookup_text(str(conductor.get("apellido") or ""))
        nombre_completo = _normalize_lookup_text(f"{nombre} {apellido}")
        cedula = _normalize_lookup_text(str(conductor.get("cedula") or ""))

        if needle in {conductor_id, nombre, apellido, nombre_completo, cedula}:
            return conductor_id

    raise ValueError("No se encontró el conductor indicado. Escribe un ID, cédula o nombre válido.")


def _resolve_user_id(raw_value: str) -> str:
    value = (raw_value or "").strip()
    if not value:
        return ""
    if value.isdigit():
        return value

    needle = _normalize_lookup_text(value)
    for user in User.list_users():
        user_id = str(user.get("id") or "").strip()
        username = _normalize_lookup_text(str(user.get("username") or ""))
        nombre = _normalize_lookup_text(str(user.get("nombre") or ""))
        apellido = _normalize_lookup_text(str(user.get("apellido") or ""))
        nombre_completo = _normalize_lookup_text(f"{nombre} {apellido}")
        email = _normalize_lookup_text(str(user.get("email") or ""))
        documento = _normalize_lookup_text(str(user.get("numero_identificacion") or ""))

        if needle in {user_id, username, nombre, apellido, nombre_completo, email, documento}:
            return user_id

    raise ValueError("No se encontró el usuario indicado. Escribe un ID, usuario, correo o nombre válido.")


def _date_to_input(raw_value) -> str:
    if raw_value in (None, ""):
        return ""
    if hasattr(raw_value, "strftime"):
        return raw_value.strftime("%Y-%m-%d")
    text = str(raw_value).strip()
    return text[:10] if len(text) >= 10 else text


def _flash_vehicle_document_alert(vehiculo_id: int) -> None:
    try:
        status = DocumentoVehiculo.get_status_summary(vehiculo_id=vehiculo_id, warning_days=WARNING_DAYS)
    except Exception:
        return

    level = (status.get("level") or "").strip().lower()
    message = (status.get("message") or "").strip()
    if message and level == "warning":
        flash(message, "warning")
    elif message and level == "error":
        flash(message, "error")


@vehiculos_bp.get("/")
@login_required
@community_required
def list_items():
    can_manage_sensitive = _can_manage_sensitive()
    placa_consulta = (request.args.get("placa", "") or "").strip().upper()
    vehiculo_consulta = None
    tipos_vehiculo = Vehiculo.list_vehicle_types()
    conductores = Conductor.list_items()
    usuarios = User.list_users()
    items = Vehiculo.list_items()

    warning_items = []
    error_items = []
    if can_manage_sensitive:
        for item in items:
            vehiculo_id = item.get("id")
            if not vehiculo_id:
                continue

            docs = DocumentoVehiculo.get_vehicle_documents(int(vehiculo_id))
            status = DocumentoVehiculo.get_status_summary(int(vehiculo_id), warning_days=WARNING_DAYS)

            item["fecha_vencimiento_soat_input"] = _date_to_input((docs.get("soat") or {}).get("fecha_vencimiento"))
            item["fecha_vencimiento_tecnomecanica_input"] = _date_to_input((docs.get("tecnomecanica") or {}).get("fecha_vencimiento"))
            item["fecha_vencimiento_tarjeta_propiedad_input"] = _date_to_input((docs.get("tarjeta_propiedad") or {}).get("fecha_vencimiento"))
            item["doc_status_level"] = status.get("level") or "success"
            item["doc_status_message"] = status.get("message") or ""
            item["conductor_ref"] = str(item.get("conductor_id") or "")
            item["user_ref"] = str(item.get("user_id") or "")

            if item["doc_status_level"] == "warning":
                warning_items.append(item)
            elif item["doc_status_level"] == "error":
                error_items.append(item)

    if placa_consulta:
        vehiculo_consulta = Vehiculo.get_by_placa(placa_consulta)

    doc_status_consulta = None
    if can_manage_sensitive and vehiculo_consulta and vehiculo_consulta.get("id"):
        try:
            doc_status_consulta = DocumentoVehiculo.get_status_summary(int(vehiculo_consulta.get("id")), warning_days=30)
        except Exception:
            doc_status_consulta = None

    return render_template(
        "vehiculos/index.html",
        placa_consulta=placa_consulta,
        vehiculo_consulta=vehiculo_consulta,
        doc_status_consulta=doc_status_consulta,
        items=items,
        warning_items=warning_items,
        error_items=error_items,
        can_manage_sensitive=can_manage_sensitive,
        tipos_vehiculo=tipos_vehiculo,
        conductores=conductores,
        usuarios=usuarios,
    )


@vehiculos_bp.post("/crear")
@login_required
@community_required
def create_item():
    if not _can_manage_sensitive():
        flash("No tienes permisos para registrar o editar información documental de vehículos.", "error")
        return redirect(url_for("vehiculos.list_items"))

    placa = Vehiculo.normalize_plate(request.form.get("placa", ""))
    tipo_vehiculo_id = request.form.get("tipo_vehiculo_id", "").strip()
    conductor_ref = request.form.get("conductor_id", "")
    user_ref = request.form.get("user_id", "")

    plate_ok, plate_error = Vehiculo.validate_plate_format(placa=placa, tipo_vehiculo_id=tipo_vehiculo_id)
    if not plate_ok:
        flash(plate_error, "error")
        return redirect(url_for("vehiculos.list_items"))

    try:
        conductor_id = _resolve_conductor_id(conductor_ref)
        user_id = _resolve_user_id(user_ref)
    except ValueError as exc:
        flash(str(exc), "error")
        return redirect(url_for("vehiculos.list_items"))

    payload = {
        "placa": placa,
        "tipo_vehiculo_id": tipo_vehiculo_id,
        "marca": request.form.get("marca", "").strip(),
        "modelo": request.form.get("modelo", "").strip(),
        "color": request.form.get("color", "").strip(),
        "fecha_registro": request.form.get("fecha_registro", "").strip(),
        "estado": request.form.get("estado", "").strip(),
        "conductor_id": conductor_id,
        "user_id": user_id,
    }

    docs_payload = {
        "soat": request.form.get("fecha_vencimiento_soat", "").strip(),
        "tecnomecanica": request.form.get("fecha_vencimiento_tecnomecanica", "").strip(),
        "tarjeta_propiedad": request.form.get("fecha_vencimiento_tarjeta_propiedad", "").strip(),
    }

    if not all(docs_payload.values()):
        flash("Debes registrar vencimiento de SOAT, técnico-mecánica y tarjeta de propiedad.", "error")
        return redirect(url_for("vehiculos.list_items"))

    try:
        vehiculo_id = Vehiculo.create_item(payload)
        if vehiculo_id:
            DocumentoVehiculo.upsert_documents(int(vehiculo_id), docs_payload)
            _flash_vehicle_document_alert(int(vehiculo_id))
        flash("Vehiculo creado correctamente.", "success")

        eval_result = HorarioOperacion.evaluate_moment()
        if eval_result.get("is_sunday") or eval_result.get("is_holiday"):
            reason = "domingo" if eval_result.get("is_sunday") else "festivo"
            fecha_hora_text = eval_result.get("now").strftime("%Y-%m-%d %H:%M:%S")
            actor_username = (getattr(current_user, "username", "") or "usuario_sistema").strip() or "usuario_sistema"

            try:
                sent = send_admin_offday_alert(
                    placa=placa,
                    actor_username=actor_username,
                    reason=reason,
                    fecha_hora_text=fecha_hora_text,
                )
                if sent:
                    flash("Se envió alerta al administrador por registro en domingo/festivo.", "warning")
                else:
                    flash("Registro en domingo/festivo detectado. Revisa configuración SMTP para alertas por correo.", "warning")
            except Exception as alert_exc:
                flash(f"Registro en domingo/festivo detectado, pero falló envío de alerta: {alert_exc}", "warning")
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
    if not _can_manage_sensitive():
        flash("No tienes permisos para actualizar información documental de otros usuarios.", "error")
        return redirect(url_for("vehiculos.list_items"))

    placa = Vehiculo.normalize_plate(request.form.get("placa", ""))
    tipo_vehiculo_id = request.form.get("tipo_vehiculo_id", "").strip()
    conductor_ref = request.form.get("conductor_id", "")
    user_ref = request.form.get("user_id", "")

    plate_ok, plate_error = Vehiculo.validate_plate_format(placa=placa, tipo_vehiculo_id=tipo_vehiculo_id)
    if not plate_ok:
        flash(plate_error, "error")
        return redirect(url_for("vehiculos.list_items"))

    try:
        conductor_id = _resolve_conductor_id(conductor_ref)
        user_id = _resolve_user_id(user_ref)
    except ValueError as exc:
        flash(str(exc), "error")
        return redirect(url_for("vehiculos.list_items"))

    payload = {
        "placa": placa,
        "tipo_vehiculo_id": tipo_vehiculo_id,
        "marca": request.form.get("marca", "").strip(),
        "modelo": request.form.get("modelo", "").strip(),
        "color": request.form.get("color", "").strip(),
        "estado": request.form.get("estado", "").strip(),
        "conductor_id": conductor_id,
        "user_id": user_id,
    }

    docs_payload = {
        "soat": request.form.get("fecha_vencimiento_soat", "").strip(),
        "tecnomecanica": request.form.get("fecha_vencimiento_tecnomecanica", "").strip(),
        "tarjeta_propiedad": request.form.get("fecha_vencimiento_tarjeta_propiedad", "").strip(),
    }

    try:
        Vehiculo.update_item(item_id=item_id, data=payload)
        if any(docs_payload.values()):
            DocumentoVehiculo.upsert_documents(int(item_id), docs_payload)
        _flash_vehicle_document_alert(int(item_id))
        flash("Vehiculo actualizado correctamente.", "success")
    except Exception as exc:
        flash(f"No se pudo actualizar vehiculo: {exc}", "error")

    return redirect(url_for("vehiculos.list_items"))

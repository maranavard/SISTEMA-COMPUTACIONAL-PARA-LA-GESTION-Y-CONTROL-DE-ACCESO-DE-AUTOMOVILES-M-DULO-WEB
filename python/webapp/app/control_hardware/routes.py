"""Pantalla y API JSON para control manual de hardware."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
from datetime import datetime
from functools import wraps
from uuid import UUID

from flask import Blueprint, abort, current_app, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.models.control_hardware import ControlHardware
from app.utils.authz import normalize_role


control_hardware_bp = Blueprint("control_hardware", __name__, url_prefix="/control-hardware")

ALLOWED_EVENT_TYPES = {"acceso_detectado", "validacion_externa", "estado_dispositivo", "heartbeat"}
ALLOWED_ACCESS_ROLES = {"admin_sistema", "admin", "administrador", "seguridad_udec", "vigilante", "vigilancia"}
INDEX_ROUTE = "control_hardware.index"


def _current_role() -> str:
    return normalize_role(getattr(current_user, "rol", ""))


def _is_admin_role() -> bool:
    return _current_role() in {"admin_sistema", "admin", "administrador"}


def control_access_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(401)

        rol = normalize_role(getattr(current_user, "rol", ""))
        if rol not in ALLOWED_ACCESS_ROLES:
            abort(403)

        return view_func(*args, **kwargs)

    return wrapper


def token_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        expected = (current_app.config.get("HARDWARE_CONTROL_TOKEN") or "").strip()
        received = (request.headers.get("X-Hardware-Token") or "").strip()

        if not expected:
            return jsonify({"ok": False, "error": "Token de control de hardware no configurado"}), 503

        if not received or received != expected:
            return jsonify({"ok": False, "error": "No autorizado"}), 401

        return view_func(*args, **kwargs)

    return wrapper


def _is_valid_uuid(value: str) -> bool:
    try:
        UUID(value)
        return True
    except (ValueError, TypeError):
        return False


def _parse_iso_datetime(value: str):
    text = (value or "").strip()
    if not text:
        return None

    normalized = text.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None


def _normalize_plate(value: str) -> str:
    return str(value or "").strip().upper()


def _validate_access_detected_payload(payload: dict) -> tuple[bool, str]:
    placa = _normalize_plate(payload.get("placa"))
    movimiento = str(payload.get("movimiento") or "").strip().lower()
    if not placa:
        return False, "payload.placa es obligatorio para acceso_detectado"
    if movimiento not in {"entrada", "salida"}:
        return False, "payload.movimiento debe ser entrada o salida"
    payload["placa"] = placa
    payload["movimiento"] = movimiento
    return True, ""


def _validate_external_validation_payload(payload: dict) -> tuple[bool, str]:
    placa = _normalize_plate(payload.get("placa"))
    resultado = str(payload.get("resultado") or "").strip().lower()
    if not placa:
        return False, "payload.placa es obligatorio para validacion_externa"
    if resultado not in {"autorizado", "rechazado", "pendiente"}:
        return False, "payload.resultado debe ser autorizado, rechazado o pendiente"
    payload["placa"] = placa
    payload["resultado"] = resultado
    return True, ""


def _validate_device_state_payload(payload: dict) -> tuple[bool, str]:
    dispositivo = str(payload.get("dispositivo") or "").strip()
    estado = str(payload.get("estado") or "").strip().lower()
    if not dispositivo:
        return False, "payload.dispositivo es obligatorio para estado_dispositivo"
    if estado not in {"on", "off"}:
        return False, "payload.estado debe ser on u off"
    payload["estado"] = estado
    return True, ""


def _validate_heartbeat_payload(payload: dict) -> tuple[bool, str]:
    status = str(payload.get("status") or "").strip().lower()
    if not status:
        return False, "payload.status es obligatorio para heartbeat"
    payload["status"] = status
    return True, ""


def _validate_event_payload(event_type: str, payload: dict) -> tuple[bool, str]:
    validators = {
        "acceso_detectado": _validate_access_detected_payload,
        "validacion_externa": _validate_external_validation_payload,
        "estado_dispositivo": _validate_device_state_payload,
        "heartbeat": _validate_heartbeat_payload,
    }
    validator = validators.get(event_type)
    if not validator:
        return False, "event_type no soportado"
    return validator(payload)


def _reject(error_message: str, status_code: int, **extra_fields):
    payload = {"ok": False, "error": error_message}
    payload.update(extra_fields)
    return False, payload, status_code


def _extract_event_fields(data: dict) -> dict:
    return {
        "event_id": str(data.get("event_id") or "").strip(),
        "event_type": str(data.get("event_type") or "").strip(),
        "source_device": str(data.get("source_device") or "").strip(),
        "occurred_at_raw": str(data.get("occurred_at") or "").strip(),
        "schema_version": str(data.get("schema_version") or "").strip(),
        "payload": data.get("payload"),
        "trace": data.get("trace"),
    }


def _validate_required_event_fields(fields: dict):
    if not fields["event_id"]:
        return _reject("Campo event_id es obligatorio", 400)
    if not _is_valid_uuid(fields["event_id"]):
        return _reject("event_id debe ser UUID valido", 422)

    if not fields["event_type"]:
        return _reject("Campo event_type es obligatorio", 400)
    if fields["event_type"] not in ALLOWED_EVENT_TYPES:
        return _reject("event_type no permitido", 422)

    if not fields["source_device"]:
        return _reject("Campo source_device es obligatorio", 400)
    if not fields["schema_version"]:
        return _reject("Campo schema_version es obligatorio", 400)

    return None


def _validate_event_objects(event_type: str, payload, trace):
    if not isinstance(payload, dict):
        return _reject("Campo payload debe ser objeto JSON", 422)
    if trace is not None and not isinstance(trace, dict):
        return _reject("Campo trace debe ser objeto JSON", 422)

    valid, validation_error = _validate_event_payload(event_type=event_type, payload=payload)
    if not valid:
        return _reject(validation_error, 422)

    return None


def _ingest_event_data(data: dict) -> tuple[bool, dict, int]:
    if not isinstance(data, dict):
        return _reject("JSON invalido", 400)

    fields = _extract_event_fields(data)

    required_error = _validate_required_event_fields(fields)
    if required_error:
        return required_error

    occurred_at = _parse_iso_datetime(fields["occurred_at_raw"])
    if not occurred_at:
        return _reject("Campo occurred_at invalido; usa ISO-8601", 422)

    objects_error = _validate_event_objects(
        event_type=fields["event_type"],
        payload=fields["payload"],
        trace=fields["trace"],
    )
    if objects_error:
        return objects_error

    inserted = ControlHardware.register_event(
        event_id=fields["event_id"],
        event_type=fields["event_type"],
        source_device=fields["source_device"],
        occurred_at=occurred_at,
        schema_version=fields["schema_version"],
        payload=fields["payload"],
        trace=fields["trace"],
    )

    if not inserted:
        return _reject("Evento duplicado", 409, event_id=fields["event_id"])

    return True, {"ok": True, "status": "accepted", "event_id": fields["event_id"]}, 202


def _resolve_shared_path(config_value: str) -> Path:
    path = Path(config_value)
    if path.is_absolute():
        return path
    return Path(current_app.root_path).parent / path


def _move_file(src: Path, target_dir: Path, prefix: str = "") -> Path:
    target_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    target_name = f"{prefix}{timestamp}_{src.name}" if prefix else f"{timestamp}_{src.name}"
    target_path = target_dir / target_name
    shutil.move(str(src), str(target_path))
    return target_path


def _process_shared_events_batch(max_files: int) -> dict:
    inbox_dir = _resolve_shared_path(current_app.config.get("HARDWARE_SHARED_INBOX", "hardware_shared/inbox"))
    processed_dir = _resolve_shared_path(current_app.config.get("HARDWARE_SHARED_PROCESSED", "hardware_shared/processed"))
    error_dir = _resolve_shared_path(current_app.config.get("HARDWARE_SHARED_ERROR", "hardware_shared/error"))

    inbox_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    error_dir.mkdir(parents=True, exist_ok=True)

    files = sorted(inbox_dir.glob("*.json"))[: max(1, int(max_files or 1))]

    report = {
        "scanned": len(files),
        "accepted": 0,
        "duplicates": 0,
        "errors": 0,
    }

    for file_path in files:
        try:
            raw = file_path.read_text(encoding="utf-8")
            data = json.loads(raw)
        except Exception:
            report["errors"] += 1
            _move_file(file_path, error_dir, prefix="json_error_")
            continue

        ok, _, status_code = _ingest_event_data(data)
        if ok:
            report["accepted"] += 1
            _move_file(file_path, processed_dir)
            continue

        if status_code == 409:
            report["duplicates"] += 1
            _move_file(file_path, processed_dir, prefix="dup_")
            continue

        report["errors"] += 1
        _move_file(file_path, error_dir, prefix="event_error_")

    return report


@control_hardware_bp.get("/")
@login_required
@control_access_required
def index():
    items = ControlHardware.list_states()
    can_audit_hardware = _is_admin_role()
    events = ControlHardware.list_recent_events(limit=40) if can_audit_hardware else []
    return render_template(
        "control_hardware/index.html",
        items=items,
        events=events,
        can_audit_hardware=can_audit_hardware,
    )


@control_hardware_bp.post("/procesar-archivos")
@login_required
@control_access_required
def procesar_archivos():
    if not _is_admin_role():
        flash("No tienes permisos para procesar eventos por archivos compartidos.", "error")
        return redirect(url_for(INDEX_ROUTE))

    max_batch = int(current_app.config.get("HARDWARE_SHARED_MAX_BATCH", 30) or 30)
    report = _process_shared_events_batch(max_files=max_batch)
    flash(
        (
            "Lote procesado: "
            f"{report['scanned']} archivos, "
            f"{report['accepted']} aceptados, "
            f"{report['duplicates']} duplicados, "
            f"{report['errors']} con error."
        ),
        "success",
    )
    return redirect(url_for(INDEX_ROUTE))


@control_hardware_bp.post("/guardar")
@login_required
@control_access_required
def guardar():
    raw_keys = request.form.getlist("encendido")
    active_keys = {item.strip() for item in raw_keys if str(item or "").strip()}

    current_items = ControlHardware.list_states()
    update_map = {item["clave"]: (item["clave"] in active_keys) for item in current_items}

    ControlHardware.update_states(update_map, user_id=int(getattr(current_user, "id", 0) or 0))
    flash("Estado de dispositivos actualizado correctamente.", "success")
    return redirect(url_for(INDEX_ROUTE))


@control_hardware_bp.get("/api/estado")
@token_required
def api_estado():
    items = ControlHardware.list_states()
    return jsonify(
        {
            "ok": True,
            "items": [
                {
                    "clave": item["clave"],
                    "nombre": item["nombre"],
                    "descripcion": item["descripcion"],
                    "encendido": item["encendido"],
                    "updated_at": item["updated_at"].isoformat() if item.get("updated_at") else None,
                }
                for item in items
            ],
        }
    )


@control_hardware_bp.post("/api/comando")
@token_required
def api_comando():
    payload = request.get_json(silent=True) or {}
    clave = str(payload.get("clave") or "").strip()

    if not clave:
        return jsonify({"ok": False, "error": "Campo clave es obligatorio"}), 400

    encendido_raw = payload.get("encendido")
    encendido = bool(encendido_raw)

    updated = ControlHardware.update_one(clave=clave, encendido=encendido, user_id=None)
    if not updated:
        return jsonify({"ok": False, "error": "Dispositivo no encontrado"}), 404

    return jsonify({"ok": True, "clave": clave, "encendido": encendido})


@control_hardware_bp.post("/api/evento")
@token_required
def api_evento():
    data = request.get_json(silent=True)
    ok, response, status_code = _ingest_event_data(data)
    return jsonify(response), status_code

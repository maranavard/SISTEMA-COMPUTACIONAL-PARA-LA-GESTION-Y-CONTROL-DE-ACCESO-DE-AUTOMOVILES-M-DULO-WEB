"""Rutas del módulo Control de Accesos."""

from functools import wraps

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.models.novedad import Novedad
from app.models.vehiculo import Vehiculo
from app.models.visitante import Visitante


control_accesos_bp = Blueprint("control_accesos", __name__, url_prefix="/control-accesos")
INDEX_ROUTE = "control_accesos.index"
AUTORIZACION_ROUTE = "control_accesos.autorizacion"
HISTORIAL_ROUTE = "control_accesos.historial"
DETALLE_TEMPLATE = "control_accesos/detalle.html"
RECORD_NOT_FOUND_MSG = "No se encontró el registro solicitado."
ALLOWED_ACCESS_ROLES = {"admin_sistema", "admin", "administrador", "seguridad_udec", "vigilante", "vigilancia"}


def _extract_primary_role(rol_raw: str) -> str:
    rol = (rol_raw or "").strip().lower()
    if rol.startswith("{") and rol.endswith("}"):
        parts = [item.strip().strip('"') for item in rol[1:-1].split(",") if item.strip()]
        return parts[0] if parts else ""
    if rol.startswith("[") and rol.endswith("]"):
        parts = [item.strip().strip('"') for item in rol[1:-1].split(",") if item.strip()]
        return parts[0] if parts else ""
    return rol


def _is_access_role_allowed(rol_raw: str) -> bool:
    return _extract_primary_role(rol_raw) in ALLOWED_ACCESS_ROLES


def control_access_required(view_func):
    """Permite acceso a roles de administración y seguridad/control."""

    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(401)

        if not _is_access_role_allowed(getattr(current_user, "rol", "")):
            abort(403)

        return view_func(*args, **kwargs)

    return wrapper


def _parse_identidad(raw_identity: str) -> tuple[str, str, str]:
    text = (raw_identity or "").strip()
    if not text:
        return "", "", ""

    if "," in text:
        parts = [part.strip() for part in text.split(",")]
    else:
        parts = text.split()

    placa = parts[0] if len(parts) > 0 else ""
    nombre = parts[1] if len(parts) > 1 else ""
    apellido = " ".join(parts[2:]) if len(parts) > 2 else ""
    return placa.upper(), nombre, apellido


def _find_visitante(item_id: int) -> dict | None:
    items = Visitante.list_items()
    for item in items:
        if int(item.get("id") or 0) == item_id:
            return item
    return None


def _flash_vehicular_error(exc: Exception) -> None:
    error_text = str(exc)
    if "No hay espacios disponibles" in error_text:
        flash("No hay espacios disponibles para permitir el ingreso.", "error")
    elif "placa" in error_text.lower() or "vehículo" in error_text.lower() or "vehiculo" in error_text.lower():
        flash("La placa no está registrada en el sistema.", "error")
    else:
        flash(f"No se pudo validar el acceso vehicular: {exc}", "error")


def _process_ingreso_vehicular(placa: str) -> str:
    doc_status = Vehiculo.get_document_status_by_placa(placa=placa, warning_days=30)
    level = (doc_status.get("level") or "").strip().lower()
    message = (doc_status.get("message") or "").strip()
    block_auto = bool(doc_status.get("block_automatic_assignment"))

    if message and level in {"warning", "error"}:
        flash(message, "warning" if level == "warning" else "error")

    if block_auto:
        return "blocked"

    result = Novedad.register_ingreso_by_placa(placa=placa, user_id=int(current_user.id))
    assigned_space = result.get("assigned_space_num")
    if not assigned_space:
        flash("No hay espacios disponibles para permitir el ingreso.", "error")
        return "blocked"

    flash(f"Ingreso validado para {placa}. Cupo asignado: {assigned_space}.", "success")
    return redirect(url_for("espacios.list_items", assigned_space=assigned_space, assigned_plate=placa))


def _process_salida_vehicular(placa: str) -> None:
    Novedad.register_salida_by_placa(placa=placa, user_id=int(current_user.id), observaciones="Salida validada en control de accesos")
    flash(f"Salida validada correctamente para la placa {placa}.", "success")


@control_accesos_bp.get("/")
@login_required
@control_access_required
def index():
    return render_template("control_accesos/index.html")


@control_accesos_bp.post("/registrar")
@login_required
@control_access_required
def registrar():
    identidad = (request.form.get("identidad", "") or "").strip()
    usuario = (request.form.get("usuario", "") or "").strip()
    espacio = (request.form.get("espacio", "") or "").strip()
    fecha_hora = (request.form.get("fecha_hora", "") or "").strip()
    accion = (request.form.get("accion", "") or "").strip()
    movimiento = (request.form.get("movimiento", "") or "").strip() or "Entrada"

    if not identidad or not espacio or not fecha_hora:
        flash("Completa los campos requeridos para registrar el acceso.", "error")
        return redirect(url_for(INDEX_ROUTE))

    placa, nombre, apellido = _parse_identidad(identidad)
    payload = {
        "nombres": nombre or "Visitante",
        "apellidos": apellido,
        "numero_identificacion": usuario,
        "area_destino": espacio,
        "motivo_visita": accion or movimiento,
        "placa": placa,
        "fecha_hora_registro": fecha_hora,
        "fecha_hora_prevista": fecha_hora,
        "estado": "pendiente_autorizacion",
        "registrado_por_usuario_id": int(current_user.id),
    }

    try:
        Visitante.create_item(payload)
        flash("Registro creado correctamente. Continúa con la autorización.", "success")
    except Exception as exc:
        flash(f"No se pudo registrar el acceso: {exc}", "error")
        return redirect(url_for(INDEX_ROUTE))

    return redirect(url_for(AUTORIZACION_ROUTE, documento=usuario))


@control_accesos_bp.post("/vehicular")
@login_required
@control_access_required
def registrar_vehicular():
    placa = (request.form.get("placa", "") or "").strip().upper()
    movimiento = (request.form.get("movimiento", "entrada") or "entrada").strip().lower()

    if not placa:
        flash("Debes indicar la placa para validar el acceso vehicular.", "error")
        return redirect(url_for(INDEX_ROUTE))

    try:
        if movimiento in {"entrada", "ingreso"}:
            ingreso_result = _process_ingreso_vehicular(placa=placa)
            if ingreso_result != "blocked":
                return ingreso_result
            return redirect(url_for(INDEX_ROUTE))

        _process_salida_vehicular(placa=placa)
    except Exception as exc:
        _flash_vehicular_error(exc)

    return redirect(url_for(INDEX_ROUTE))


@control_accesos_bp.get("/historial")
@login_required
@control_access_required
def historial():
    items = Visitante.list_items()
    return render_template("control_accesos/historial.html", items=items)


@control_accesos_bp.get("/historial/<int:item_id>/visualizar")
@login_required
@control_access_required
def historial_visualizar(item_id: int):
    item = _find_visitante(item_id)
    if not item:
        flash(RECORD_NOT_FOUND_MSG, "error")
        return redirect(url_for(HISTORIAL_ROUTE))

    return render_template(DETALLE_TEMPLATE, item=item, printable=False)


@control_accesos_bp.get("/historial/<int:item_id>/pdf")
@login_required
@control_access_required
def historial_pdf(item_id: int):
    item = _find_visitante(item_id)
    if not item:
        flash(RECORD_NOT_FOUND_MSG, "error")
        return redirect(url_for(HISTORIAL_ROUTE))

    return render_template(DETALLE_TEMPLATE, item=item, printable=True)


@control_accesos_bp.get("/autorizacion")
@login_required
@control_access_required
def autorizacion():
    documento = (request.args.get("documento", "") or "").strip()
    selected_id_raw = (request.args.get("id", "") or "").strip()
    items = Visitante.list_items()

    excluded_states = {"autorizado", "rechazado"}
    filtered = [
        item
        for item in items
        if (item.get("estado") or "").strip().lower() not in excluded_states
    ]

    if documento:
        filtered = [
            item
            for item in filtered
            if documento.lower() in str(item.get("numero_identificacion") or "").lower()
        ]

    selected_item = None
    if selected_id_raw:
        try:
            selected_id = int(selected_id_raw)
            selected_item = next((item for item in filtered if int(item.get("id") or 0) == selected_id), None)
        except ValueError:
            selected_item = None

    if not selected_item and filtered:
        selected_item = filtered[0]

    return render_template(
        "control_accesos/autorizacion.html",
        items=filtered,
        documento=documento,
        selected_item=selected_item,
    )


@control_accesos_bp.post("/autorizacion/<int:item_id>/autorizar")
@login_required
@control_access_required
def autorizar(item_id: int):
    try:
        Visitante.update_item(item_id, {"estado": "autorizado"})
        flash("Ingreso autorizado correctamente.", "success")
    except Exception as exc:
        flash(f"No se pudo autorizar el ingreso: {exc}", "error")

    return redirect(url_for(AUTORIZACION_ROUTE))


@control_accesos_bp.post("/autorizacion/<int:item_id>/rechazar")
@login_required
@control_access_required
def rechazar(item_id: int):
    try:
        Visitante.update_item(item_id, {"estado": "rechazado"})
        flash("Solicitud rechazada correctamente.", "success")
    except Exception as exc:
        flash(f"No se pudo rechazar la solicitud: {exc}", "error")

    return redirect(url_for(AUTORIZACION_ROUTE))


@control_accesos_bp.get("/autorizacion/<int:item_id>/detalle")
@login_required
@control_access_required
def autorizacion_detalle(item_id: int):
    item = _find_visitante(item_id)
    if not item:
        flash(RECORD_NOT_FOUND_MSG, "error")
        return redirect(url_for(AUTORIZACION_ROUTE))

    return render_template(DETALLE_TEMPLATE, item=item, printable=False)

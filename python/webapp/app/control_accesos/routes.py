"""Rutas del módulo Control de Accesos."""

from functools import wraps

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.models.visitante import Visitante


control_accesos_bp = Blueprint("control_accesos", __name__, url_prefix="/control-accesos")


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
        return redirect(url_for("control_accesos.index"))

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
        return redirect(url_for("control_accesos.index"))

    return redirect(url_for("control_accesos.autorizacion", documento=usuario))


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
        flash("No se encontró el registro solicitado.", "error")
        return redirect(url_for("control_accesos.historial"))

    return render_template("control_accesos/detalle.html", item=item, printable=False)


@control_accesos_bp.get("/historial/<int:item_id>/pdf")
@login_required
@control_access_required
def historial_pdf(item_id: int):
    item = _find_visitante(item_id)
    if not item:
        flash("No se encontró el registro solicitado.", "error")
        return redirect(url_for("control_accesos.historial"))

    return render_template("control_accesos/detalle.html", item=item, printable=True)


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

    return redirect(url_for("control_accesos.autorizacion"))


@control_accesos_bp.post("/autorizacion/<int:item_id>/rechazar")
@login_required
@control_access_required
def rechazar(item_id: int):
    try:
        Visitante.update_item(item_id, {"estado": "rechazado"})
        flash("Solicitud rechazada correctamente.", "success")
    except Exception as exc:
        flash(f"No se pudo rechazar la solicitud: {exc}", "error")

    return redirect(url_for("control_accesos.autorizacion"))


@control_accesos_bp.get("/autorizacion/<int:item_id>/detalle")
@login_required
@control_access_required
def autorizacion_detalle(item_id: int):
    item = _find_visitante(item_id)
    if not item:
        flash("No se encontró el registro solicitado.", "error")
        return redirect(url_for("control_accesos.autorizacion"))

    return render_template("control_accesos/detalle.html", item=item, printable=False)

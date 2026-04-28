"""Rutas del módulo de gestión de reportes."""

from __future__ import annotations

import json
from datetime import date, datetime
from functools import wraps
from io import BytesIO

from flask import Blueprint, Response, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from openpyxl import Workbook

from app.models.novedad import Novedad
from app.models.user import User
from app.models.vehiculo import Vehiculo
from app.utils.authz import normalize_role


reportes_bp = Blueprint("reportes", __name__, url_prefix="/reportes")


def _current_role() -> str:
    return normalize_role(getattr(current_user, "rol", ""))


def _is_guard_role() -> bool:
    return _current_role() in {"vigilante", "vigilancia", "seguridad_udec"}


def _is_admin_role() -> bool:
    return _current_role() in {"admin_sistema", "admin", "administrador"}


def control_access_required(view_func):
    """Permite acceso a roles de administración y seguridad/control."""

    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(401)

        rol = _current_role()

        allowed = {"admin_sistema", "admin", "administrador", "seguridad_udec", "vigilante", "vigilancia"}
        if rol not in allowed:
            abort(403)

        return view_func(*args, **kwargs)

    return wrapper


def _normalize_text(value) -> str:
    return str(value or "").strip().lower()


def _parse_filters_from_request() -> dict:
    return {
        "placa": (request.args.get("placa", "") or "").strip().upper(),
        "fecha": (request.args.get("fecha", "") or "").strip(),
        "usuario": (request.args.get("usuario", "") or "").strip(),
        "vigilante": (request.args.get("vigilante", "") or "").strip(),
    }


def _user_lookup() -> dict[int, dict]:
    users = User.list_users()
    lookup: dict[int, dict] = {}
    for item in users:
        try:
            user_id = int(item.get("id"))
        except Exception:
            continue

        nombre = str(item.get("nombre") or "").strip()
        apellido = str(item.get("apellido") or "").strip()
        username = str(item.get("username") or "").strip()
        role = str(item.get("rol") or "").strip().lower()

        display = (f"{nombre} {apellido}".strip() or username or f"Usuario {user_id}")
        nombre_display = nombre or username or f"Usuario {user_id}"
        lookup[user_id] = {
            "display": display,
            "nombre": nombre_display,
            "apellido": apellido,
            "username": username,
            "role": role,
        }

    return lookup


def _load_accesos_salidas(filters: dict | None = None) -> list[dict]:
    rows = Novedad.list_recent(limit=500)
    report_rows = []
    users = _user_lookup()
    filters = filters or {}

    placa_filter = _normalize_text(filters.get("placa"))
    fecha_filter = _normalize_text(filters.get("fecha"))
    usuario_filter = _normalize_text(filters.get("usuario"))
    vigilante_filter = _normalize_text(filters.get("vigilante"))
    only_today = _is_guard_role()
    today_text = date.today().strftime("%Y-%m-%d") if only_today else ""

    for row in rows:
        tipo = (row.get("tipo_novedad") or "").strip().lower()
        user_id = row.get("id_usuario")

        try:
            user_id_int = int(user_id) if user_id not in (None, "") else None
        except Exception:
            user_id_int = None

        user_data = users.get(user_id_int or -1, {})
        usuario_display = user_data.get("display") or ""
        usuario_nombre = user_data.get("nombre") or ""
        usuario_apellido = user_data.get("apellido") or ""
        usuario_role = user_data.get("role") or ""
        is_vigilante = usuario_role in {"vigilante", "vigilancia", "seguridad_udec"}
        vigilante_display = usuario_display if is_vigilante else ""
        vigilante_nombre = usuario_nombre if is_vigilante else ""
        vigilante_apellido = usuario_apellido if is_vigilante else ""

        fecha_hora = row.get("fecha_hora")
        fecha_text = ""
        if hasattr(fecha_hora, "strftime"):
            fecha_text = fecha_hora.strftime("%Y-%m-%d")
        else:
            fecha_text = str(fecha_hora or "")[:10]

        if only_today and fecha_text != today_text:
            continue

        placa_text = str(row.get("placa") or "")

        if placa_filter and placa_filter not in _normalize_text(placa_text):
            continue
        if fecha_filter and fecha_filter != _normalize_text(fecha_text):
            continue
        if usuario_filter:
            hay_usuario = usuario_filter in _normalize_text(usuario_display) or usuario_filter in _normalize_text(user_id)
            if not hay_usuario:
                continue
        if vigilante_filter:
            if vigilante_filter not in _normalize_text(vigilante_display):
                continue

        report_rows.append(
            {
                "id_novedad": row.get("id"),
                "tipo_movimiento": tipo or "novedad",
                "placa": placa_text,
                "fecha_hora": fecha_hora or "",
                "estado": row.get("estado") or "",
                "observaciones": row.get("observaciones") or "",
                "usuario_nombre": usuario_nombre,
                "usuario_apellido": usuario_apellido,
                "vigilante_nombre": vigilante_nombre,
                "vigilante_apellido": vigilante_apellido,
            }
        )

    return report_rows


def _load_vehiculos(filters: dict | None = None) -> list[dict]:
    rows = Vehiculo.list_items()
    report_rows = []
    filters = filters or {}

    placa_filter = _normalize_text(filters.get("placa"))
    fecha_filter = _normalize_text(filters.get("fecha"))

    for row in rows:
        placa_text = str(row.get("placa") or "")
        fecha_registro = row.get("fecha_registro") or ""

        if hasattr(fecha_registro, "strftime"):
            fecha_registro_text = fecha_registro.strftime("%Y-%m-%d")
        else:
            fecha_registro_text = str(fecha_registro)[:10]

        if placa_filter and placa_filter not in _normalize_text(placa_text):
            continue
        if fecha_filter and fecha_filter != _normalize_text(fecha_registro_text):
            continue

        report_rows.append(
            {
                "id_vehiculo": row.get("id"),
                "placa": placa_text,
                "tipo_vehiculo": row.get("tipo_vehiculo_nombre") or "",
                "marca": row.get("marca") or "",
                "modelo": row.get("modelo") or "",
                "color": row.get("color") or "",
                "estado": row.get("estado") or "",
                "fecha_registro": fecha_registro,
            }
        )

    return report_rows


REPORT_DEFINITIONS = {
    "accesos_salidas": {
        "label": "Accesos y Salidas",
        "description": "Visualización y revisión de los accesos y salidas registrados por placa.",
        "parameters": "Tipo movimiento, placa, fecha",
        "loader": _load_accesos_salidas,
    },
    "vehiculos": {
        "label": "Vehículos",
        "description": "Reporte general de vehículos registrados en el sistema.",
        "parameters": "Placa, tipo, estado",
        "loader": _load_vehiculos,
    },
}


def _get_module_key(module_key: str) -> str:
    key = (module_key or "").strip().lower()
    if key not in REPORT_DEFINITIONS:
        raise ValueError("Módulo de reporte no soportado")
    return key


def _load_rows(module_key: str) -> tuple[dict, list[dict], list[str], dict]:
    key = _get_module_key(module_key)
    if _is_guard_role() and key != "accesos_salidas":
        raise PermissionError("El perfil vigilante solo puede consultar reportes operativos del dia.")

    definition = REPORT_DEFINITIONS[key]
    filters = _parse_filters_from_request()
    rows = definition["loader"](filters) or []

    columns = []
    if rows:
        columns = list(rows[0].keys())

    return definition, rows, columns, filters


def _excel_cell_value(value):
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(value, date):
        return value.strftime("%Y-%m-%d")
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return "" if value is None else str(value)


@reportes_bp.get("/")
@login_required
@control_access_required
def gestion():
    is_guard_role = _is_guard_role()
    modules = []
    for key, value in REPORT_DEFINITIONS.items():
        if is_guard_role and key != "accesos_salidas":
            continue
        modules.append({"key": key, **value})

    return render_template("reportes/gestion.html", modules=modules, can_export=not is_guard_role)


@reportes_bp.get("/modulo/<module_key>")
@login_required
@control_access_required
def visualizar(module_key: str):
    try:
        definition, rows, columns, filters = _load_rows(module_key)
    except Exception as exc:
        flash(f"No se pudo cargar el reporte: {exc}", "error")
        return redirect(url_for("reportes.gestion"))

    return render_template(
        "reportes/preview.html",
        report=definition,
        rows=rows,
        columns=columns,
        module_key=module_key,
        filters=filters,
        printable=False,
        can_export=not _is_guard_role(),
        is_guard_role=_is_guard_role(),
    )


@reportes_bp.get("/modulo/<module_key>/imprimir")
@login_required
@control_access_required
def imprimir(module_key: str):
    if _is_guard_role():
        flash("No tienes permisos para exportar reportes.", "error")
        return redirect(url_for("reportes.gestion"))

    try:
        definition, rows, columns, filters = _load_rows(module_key)
    except Exception as exc:
        flash(f"No se pudo preparar la impresión: {exc}", "error")
        return redirect(url_for("reportes.gestion"))

    return render_template(
        "reportes/preview.html",
        report=definition,
        rows=rows,
        columns=columns,
        module_key=module_key,
        filters=filters,
        printable=True,
    )


@reportes_bp.get("/modulo/<module_key>/excel")
@login_required
@control_access_required
def descargar_excel(module_key: str):
    if _is_guard_role():
        flash("No tienes permisos para exportar reportes.", "error")
        return redirect(url_for("reportes.gestion"))

    try:
        definition, rows, columns, _ = _load_rows(module_key)
    except Exception as exc:
        flash(f"No se pudo generar el archivo Excel: {exc}", "error")
        return redirect(url_for("reportes.gestion"))

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Reporte"

    if columns:
        sheet.append(columns)
        for row in rows:
            sheet.append([_excel_cell_value(row.get(column, "")) for column in columns])

    output = BytesIO()
    workbook.save(output)
    output.seek(0)
    filename = f"reporte_{module_key}.xlsx"

    headers = {
        "Content-Disposition": f"attachment; filename={filename}",
        "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    }
    return Response(output.getvalue(), headers=headers)

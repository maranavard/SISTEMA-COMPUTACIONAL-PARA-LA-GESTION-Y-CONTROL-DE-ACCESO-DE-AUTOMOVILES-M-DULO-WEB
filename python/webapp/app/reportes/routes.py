"""Rutas del módulo de gestión de reportes."""

from __future__ import annotations

import json
from datetime import date, datetime
from functools import wraps
from io import BytesIO

from flask import Blueprint, Response, abort, flash, redirect, render_template, url_for
from flask_login import current_user, login_required
from openpyxl import Workbook

from app.models.novedad import Novedad
from app.models.vehiculo import Vehiculo


reportes_bp = Blueprint("reportes", __name__, url_prefix="/reportes")


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


def _load_accesos_salidas() -> list[dict]:
    rows = Novedad.list_recent(limit=500)
    report_rows = []

    for row in rows:
        tipo = (row.get("tipo_novedad") or "").strip().lower()

        report_rows.append(
            {
                "id_novedad": row.get("id"),
                "tipo_movimiento": tipo or "novedad",
                "placa": row.get("placa") or "",
                "fecha_hora": row.get("fecha_hora") or "",
                "estado": row.get("estado") or "",
                "observaciones": row.get("observaciones") or "",
                "usuario_id": row.get("id_usuario") or "",
            }
        )

    return report_rows


def _load_vehiculos() -> list[dict]:
    rows = Vehiculo.list_items()
    report_rows = []

    for row in rows:
        report_rows.append(
            {
                "id_vehiculo": row.get("id"),
                "placa": row.get("placa") or "",
                "tipo_vehiculo": row.get("tipo_vehiculo_nombre") or "",
                "marca": row.get("marca") or "",
                "modelo": row.get("modelo") or "",
                "color": row.get("color") or "",
                "estado": row.get("estado") or "",
                "fecha_registro": row.get("fecha_registro") or "",
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


def _load_rows(module_key: str) -> tuple[dict, list[dict], list[str]]:
    key = _get_module_key(module_key)
    definition = REPORT_DEFINITIONS[key]
    rows = definition["loader"]() or []

    columns = []
    if rows:
        columns = list(rows[0].keys())

    return definition, rows, columns


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
    modules = [
        {"key": key, **value}
        for key, value in REPORT_DEFINITIONS.items()
    ]
    return render_template("reportes/gestion.html", modules=modules)


@reportes_bp.get("/modulo/<module_key>")
@login_required
@control_access_required
def visualizar(module_key: str):
    try:
        definition, rows, columns = _load_rows(module_key)
    except Exception as exc:
        flash(f"No se pudo cargar el reporte: {exc}", "error")
        return redirect(url_for("reportes.gestion"))

    return render_template(
        "reportes/preview.html",
        report=definition,
        rows=rows,
        columns=columns,
        module_key=module_key,
        printable=False,
    )


@reportes_bp.get("/modulo/<module_key>/imprimir")
@login_required
@control_access_required
def imprimir(module_key: str):
    try:
        definition, rows, columns = _load_rows(module_key)
    except Exception as exc:
        flash(f"No se pudo preparar la impresión: {exc}", "error")
        return redirect(url_for("reportes.gestion"))

    return render_template(
        "reportes/preview.html",
        report=definition,
        rows=rows,
        columns=columns,
        module_key=module_key,
        printable=True,
    )


@reportes_bp.get("/modulo/<module_key>/excel")
@login_required
@control_access_required
def descargar_excel(module_key: str):
    try:
        definition, rows, columns = _load_rows(module_key)
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

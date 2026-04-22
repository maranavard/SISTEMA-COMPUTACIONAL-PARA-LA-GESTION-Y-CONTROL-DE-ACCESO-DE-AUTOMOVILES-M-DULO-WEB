"""Rutas de configuración de horario operativo (solo admin)."""

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required

from app.models.horario import HorarioOperacion
from app.utils.authz import admin_required


horarios_bp = Blueprint("horarios", __name__, url_prefix="/horarios")


@horarios_bp.get("/")
@login_required
@admin_required
def index():
    config = HorarioOperacion.get_config()
    festivos_lines = [
        f"{item['fecha'].isoformat()} | {item['descripcion']}".rstrip(" |")
        for item in config.get("festivos", [])
    ]

    dias_catalogo = [
        {"id": 0, "label": "Lunes"},
        {"id": 1, "label": "Martes"},
        {"id": 2, "label": "Miércoles"},
        {"id": 3, "label": "Jueves"},
        {"id": 4, "label": "Viernes"},
        {"id": 5, "label": "Sábado"},
        {"id": 6, "label": "Domingo"},
    ]

    return render_template(
        "horarios/index.html",
        config=config,
        dias_catalogo=dias_catalogo,
        festivos_texto="\n".join(festivos_lines),
    )


@horarios_bp.post("/guardar")
@login_required
@admin_required
def guardar():
    hora_inicio = (request.form.get("hora_inicio", "") or "").strip() or HorarioOperacion.DEFAULT_HORA_INICIO
    hora_fin = (request.form.get("hora_fin", "") or "").strip() or HorarioOperacion.DEFAULT_HORA_FIN

    raw_dias = request.form.getlist("dias_activos")
    dias_activos: list[int] = []
    for item in raw_dias:
        try:
            value = int(str(item).strip())
        except ValueError:
            continue
        if 0 <= value <= 6 and value not in dias_activos:
            dias_activos.append(value)

    festivos_texto = request.form.get("festivos", "") or ""

    try:
        HorarioOperacion.update_config(
            hora_inicio=hora_inicio,
            hora_fin=hora_fin,
            dias_activos=dias_activos,
            festivos_texto=festivos_texto,
        )
        flash("Configuración de horario actualizada correctamente.", "success")
    except Exception as exc:
        flash(f"No se pudo actualizar la configuración de horarios: {exc}", "error")

    return redirect(url_for("horarios.index"))
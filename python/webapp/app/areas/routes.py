"""Rutas de administracion del catalogo de areas destino."""

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required

from app.models.area_destino import AreaDestino
from app.utils.authz import admin_required


areas_bp = Blueprint("areas", __name__, url_prefix="/areas")


@areas_bp.get("/")
@login_required
@admin_required
def index():
    areas = AreaDestino.list_items(include_inactive=True)
    return render_template("areas/index.html", areas=areas)


@areas_bp.post("/crear")
@login_required
@admin_required
def crear():
    nombre = (request.form.get("nombre", "") or "").strip()

    try:
        AreaDestino.create_area(nombre)
        flash("Area creada correctamente.", "success")
    except Exception as exc:
        if "duplicate key" in str(exc).lower() or "unique" in str(exc).lower():
            flash("Ya existe un area con ese nombre.", "error")
        else:
            flash(f"No se pudo crear el area: {exc}", "error")

    return redirect(url_for("areas.index"))


@areas_bp.post("/<int:area_id>/actualizar")
@login_required
@admin_required
def actualizar(area_id: int):
    nombre = (request.form.get("nombre", "") or "").strip()

    try:
        AreaDestino.update_area(area_id=area_id, nombre=nombre)
        flash("Area actualizada correctamente.", "success")
    except Exception as exc:
        if "duplicate key" in str(exc).lower() or "unique" in str(exc).lower():
            flash("Ya existe un area con ese nombre.", "error")
        else:
            flash(f"No se pudo actualizar el area: {exc}", "error")

    return redirect(url_for("areas.index"))



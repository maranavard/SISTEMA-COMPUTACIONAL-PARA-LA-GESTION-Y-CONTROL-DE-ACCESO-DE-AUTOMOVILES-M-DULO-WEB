"""CRUD de espacios (Sprint 1)."""

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.models.espacio import Espacio
from app.models.novedad import Novedad
from app.models.vehiculo import Vehiculo
from app.utils.lstm_predict import predict_next_40_minutes
from app.utils.authz import admin_required


espacios_bp = Blueprint("espacios", __name__, url_prefix="/espacios")


@espacios_bp.get("/")
@login_required
@admin_required
def list_items():
    items = Espacio.list_items()
    slots = Espacio.build_slots(total_slots=50)
    summary = Espacio.slot_summary(slots)

    assigned_space = (request.args.get("assigned_space", "") or "").strip()
    assigned_plate = (request.args.get("assigned_plate", "") or "").strip()
    assignment_notice = None
    if assigned_space and assigned_plate:
        assignment_notice = {
            "space": assigned_space,
            "plate": assigned_plate,
        }

    try:
        # Predicción silenciosa para mantener el modelo operativo sin botones en UI.
        predict_next_40_minutes()
    except Exception:
        pass

    recent_raw = Novedad.list_recent(limit=150)
    space_by_id = {}
    for item in items:
        if item.get("id") is not None:
            space_by_id[int(item["id"])] = item.get("numero")

    recent_ingresos = []
    latest_plate_by_space: dict[str, str] = {}
    for row in recent_raw:
        tipo = (row.get("tipo_novedad") or "").strip().lower()
        if tipo not in {"ingreso", "entrada"}:
            continue

        fecha = row.get("fecha_hora")
        fecha_texto = str(fecha or "")
        hora_ingreso = fecha.strftime("%H:%M:%S") if hasattr(fecha, "strftime") else ""

        space_num = row.get("espacio_numero")
        if space_num in (None, ""):
            space_id = row.get("id_espacio")
            if space_id is not None:
                try:
                    space_num = space_by_id.get(int(space_id), space_id)
                except Exception:
                    space_num = space_id

        if space_num:
            key_num = str(space_num)
            if key_num not in latest_plate_by_space and row.get("placa"):
                latest_plate_by_space[key_num] = str(row.get("placa"))

        recent_ingresos.append(
            {
                "placa": row.get("placa") or "",
                "espacio": space_num or "",
                "hora_ingreso": hora_ingreso,
                "fecha_hora": fecha_texto,
            }
        )

    recent_ingresos = recent_ingresos[:25]

    table_items = []
    for item in items:
        numero = str(item.get("numero") or "")
        placa_display = latest_plate_by_space.get(numero)
        if not placa_display:
            placa_display = item.get("estado") or ""
        table_items.append(
            {
                **item,
                "placa_display": placa_display,
            }
        )

    def _item_sort_key(entry: dict):
        try:
            return int(str(entry.get("numero") or "0"))
        except Exception:
            return 0

    table_items.sort(key=_item_sort_key)

    return render_template(
        "espacios/index.html",
        items=items,
        table_items=table_items,
        slots=slots,
        summary=summary,
        assignment_notice=assignment_notice,
        recent_ingresos=recent_ingresos,
    )


@espacios_bp.post("/crear")
@login_required
@admin_required
def create_item():
    payload = {
        "numero": request.form.get("numero", "").strip(),
        "estado": request.form.get("estado", "").strip(),
        "tipo_vehiculo_id": request.form.get("tipo_vehiculo_id", "").strip(),
        "fecha_actualizacion": request.form.get("fecha_actualizacion", "").strip(),
    }

    try:
        Espacio.create_item(payload)
        flash("Espacio creado correctamente.", "success")
    except Exception as exc:
        flash(f"No se pudo crear espacio: {exc}", "error")

    return redirect(url_for("espacios.list_items"))


@espacios_bp.post("/registrar")
@login_required
@admin_required
def upsert_slot():
    numero = (request.form.get("numero", "") or "").strip()
    estado_solicitado = (request.form.get("estado", "") or "").strip().lower() or "disponible"
    tipo_vehiculo_id = (request.form.get("tipo_vehiculo_id", "") or "").strip()

    estado_db, was_mapped = Espacio.adapt_estado_for_db(estado_solicitado)

    payload = {
        "numero": numero,
        "estado": estado_db,
        "tipo_vehiculo_id": tipo_vehiculo_id,
    }

    try:
        Espacio.upsert_by_numero(payload)
        if was_mapped:
            flash(
                f"Espacio {numero} guardado. Estado solicitado '{estado_solicitado}' ajustado a '{estado_db}' por reglas de BD.",
                "success",
            )
        else:
            flash(f"Espacio {numero} actualizado como {estado_db}.", "success")
    except Exception as exc:
        flash(f"No se pudo registrar el espacio: {exc}", "error")

    return redirect(url_for("espacios.list_items"))


@espacios_bp.post("/<int:item_id>/actualizar")
@login_required
@admin_required
def update_item(item_id: int):
    payload = {
        "numero": request.form.get("numero", "").strip(),
        "estado": request.form.get("estado", "").strip(),
        "tipo_vehiculo_id": request.form.get("tipo_vehiculo_id", "").strip(),
        "fecha_actualizacion": request.form.get("fecha_actualizacion", "").strip(),
    }

    try:
        Espacio.update_item(item_id=item_id, data=payload)
        flash("Espacio actualizado correctamente.", "success")
    except Exception as exc:
        flash(f"No se pudo actualizar espacio: {exc}", "error")

    return redirect(url_for("espacios.list_items"))


@espacios_bp.get("/<int:item_id>/visualizar")
@login_required
@admin_required
def visualizar_item(item_id: int):
    item = Espacio.get_by_id(item_id)
    if not item:
        flash("No se encontró el espacio solicitado.", "error")
        return redirect(url_for("espacios.list_items"))

    return render_template("espacios/view.html", item=item)


@espacios_bp.get("/<int:item_id>/editar")
@login_required
@admin_required
def editar_item(item_id: int):
    item = Espacio.get_by_id(item_id)
    if not item:
        flash("No se encontró el espacio para editar.", "error")
        return redirect(url_for("espacios.list_items"))

    return render_template("espacios/edit.html", item=item)


@espacios_bp.post("/<int:item_id>/editar")
@login_required
@admin_required
def guardar_edicion(item_id: int):
    estado_solicitado = (request.form.get("estado", "") or "").strip().lower() or "disponible"
    estado_db, _ = Espacio.adapt_estado_for_db(estado_solicitado)

    payload = {
        "numero": (request.form.get("numero", "") or "").strip(),
        "estado": estado_db,
        "tipo_vehiculo_id": (request.form.get("tipo_vehiculo_id", "") or "").strip(),
        "fecha_actualizacion": (request.form.get("fecha_actualizacion", "") or "").strip(),
    }

    try:
        Espacio.update_item(item_id=item_id, data=payload)
        flash("Espacio actualizado correctamente.", "success")
    except Exception as exc:
        flash(f"No se pudo actualizar el espacio: {exc}", "error")

    return redirect(url_for("espacios.list_items"))


@espacios_bp.post("/<int:item_id>/borrar")
@login_required
@admin_required
def borrar_item(item_id: int):
    try:
        Espacio.delete_item(item_id)
        flash("Espacio eliminado correctamente.", "success")
    except Exception as exc:
        flash(f"No se pudo eliminar el espacio: {exc}", "error")

    return redirect(url_for("espacios.list_items"))


@espacios_bp.post("/asignacion-automatica")
@login_required
@admin_required
def asignacion_automatica():
    placa = (request.form.get("placa", "") or "").strip().upper()
    if not placa:
        flash("Debes indicar una placa para asignar espacio automáticamente.", "error")
        return redirect(url_for("espacios.list_items"))

    try:
        doc_status = Vehiculo.get_document_status_by_placa(placa=placa, warning_days=30)
        level = (doc_status.get("level") or "").strip().lower()
        message = (doc_status.get("message") or "").strip()
        block_auto = bool(doc_status.get("block_automatic_assignment"))

        if message and level in {"warning", "error"}:
            flash(message, "warning" if level == "warning" else "error")

        if block_auto:
            return redirect(url_for("espacios.list_items"))
    except Exception as exc:
        flash(f"No se pudo validar documentación para la placa {placa}: {exc}", "error")
        return redirect(url_for("espacios.list_items"))

    try:
        result = Novedad.register_ingreso_by_placa(placa=placa, user_id=int(current_user.id))
        if not result.get("assigned_space_num"):
            flash("No hay espacios disponibles para asignar en este momento.", "error")
            return redirect(url_for("espacios.list_items"))
        else:
            space_num = result.get("assigned_space_num")
            try:
                pred = predict_next_40_minutes()
                if int(pred.get("maximo") or 0) >= 45:
                    flash("Alerta de ocupación: se prevé alta demanda en los próximos 40 minutos.", "error")
            except Exception:
                pass

            return redirect(
                url_for(
                    "espacios.list_items",
                    assigned_space=space_num,
                    assigned_plate=placa,
                )
            )
    except Exception as exc:
        error_text = str(exc)
        if "No hay espacios disponibles" in error_text:
            flash("No hay espacios disponibles para asignar en este momento.", "error")
        elif "placa" in error_text.lower() or "vehículo" in error_text.lower() or "vehiculo" in error_text.lower():
            flash("La placa no está registrada en la base de datos. Debes registrar el vehículo primero.", "error")
        else:
            flash(f"No se pudo ejecutar la asignación automática: {exc}", "error")

    return redirect(url_for("espacios.list_items"))

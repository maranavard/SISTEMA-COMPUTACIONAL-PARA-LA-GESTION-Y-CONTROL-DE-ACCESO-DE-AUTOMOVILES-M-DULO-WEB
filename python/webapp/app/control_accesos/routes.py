from io import BytesIO
from datetime import datetime

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)
from flask_login import current_user, login_required
from openpyxl import Workbook
from reportlab.lib.pagesizes import letter, landscape
from reportlab.pdfgen import canvas

from app.models.novedad import Novedad
from app.utils.authz import community_required

control_accesos_bp = Blueprint("control_accesos", __name__, url_prefix="/control-accesos")


@control_accesos_bp.get("/")
@login_required
@community_required
def index():
    return render_template("control_accesos/index.html")


@control_accesos_bp.post("/registrar")
@login_required
@community_required
def registrar():
    flash("Registro manual no implementado en esta versión.", "info")
    return redirect(url_for("control_accesos.index"))


@control_accesos_bp.post("/registrar-vehicular")
@login_required
@community_required
def registrar_vehicular():
    placa = (request.form.get("placa", "") or "").strip().upper()
    movimiento = (request.form.get("movimiento", "") or "").strip().lower()

    if not placa:
        flash("Debes ingresar una placa.", "error")
        return redirect(url_for("control_accesos.index"))

    try:
        if movimiento in {"entrada", "ingreso"}:
            result = Novedad.register_ingreso_by_placa(placa=placa, user_id=int(current_user.id))
            flash(
                f"Ingreso registrado correctamente. Espacio asignado: {result.get('assigned_space_num') or 'Sin espacio'}",
                "success",
            )
        elif movimiento == "salida":
            Novedad.register_salida_by_placa(placa=placa, user_id=int(current_user.id))
            flash("Salida registrada correctamente.", "success")
        else:
            flash("Movimiento inválido. Usa entrada o salida.", "error")
    except Exception as exc:
        flash(f"No se pudo registrar el acceso vehicular: {exc}", "error")

    return redirect(url_for("control_accesos.index"))


@control_accesos_bp.get("/autorizacion")
@login_required
@community_required
def autorizacion():
    return render_template("control_accesos/autorizacion.html")


def _get_historial_items():
    placa = (request.args.get("placa", "") or "").strip().upper()
    fecha = (request.args.get("fecha", "") or "").strip()
    documento = (request.args.get("documento", "") or "").strip()

    items = Novedad.search_access_history(
        placa=placa,
        fecha=fecha,
        documento=documento,
    )
    return placa, fecha, documento, items


def _filter_selected_items(items: list[dict]) -> list[dict]:
    selected_ids = {str(item_id) for item_id in request.args.getlist("selected_ids") if str(item_id).strip()}
    if not selected_ids:
        return items
    return [item for item in items if str(item.get("id")) in selected_ids]


@control_accesos_bp.get("/historial")
@login_required
@community_required
def historial():
    try:
        placa, fecha, documento, items = _get_historial_items()
    except Exception as exc:
        flash(f"No se pudo cargar el historial de accesos: {exc}", "error")
        placa, fecha, documento, items = "", "", "", []

    return render_template(
        "control_accesos/historial.html",
        items=items,
        placa=placa,
        fecha=fecha,
        documento=documento,
    )


@control_accesos_bp.get("/historial/export/excel")
@login_required
@community_required
def export_historial_excel():
    placa, fecha, documento, items = _get_historial_items()
    items = _filter_selected_items(items)

    wb = Workbook()
    ws = wb.active
    ws.title = "Historial Accesos"

    headers = [
        "Fecha y hora",
        "Placa",
        "Movimiento",
        "Espacio",
        "Usuario",
        "Cédula",
        "Estado",
        "Observaciones",
    ]
    ws.append(headers)

    for item in items:
        ws.append(
            [
                str(item.get("fecha_hora") or ""),
                str(item.get("placa") or ""),
                str(item.get("tipo_novedad") or ""),
                str(item.get("espacio_numero") or ""),
                str(item.get("username") or ""),
                str(item.get("documento_usuario") or ""),
                str(item.get("estado") or ""),
                str(item.get("observaciones") or ""),
            ]
        )

    output = BytesIO()
    wb.save(output)
    output.seek(0)

    filename = f"historial_accesos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    return send_file(
        output,
        as_attachment=True,
        download_name=filename,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@control_accesos_bp.get("/historial/export/pdf")
@login_required
@community_required
def export_historial_pdf():
    placa, fecha, documento, items = _get_historial_items()
    items = _filter_selected_items(items)

    output = BytesIO()
    pdf = canvas.Canvas(output, pagesize=landscape(letter))
    width, height = landscape(letter)

    pdf.setTitle("Historial de Accesos")
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(40, height - 40, "Historial de Ingresos y Salidas")

    pdf.setFont("Helvetica", 9)
    filtros = f"Filtros -> Placa: {placa or '-'} | Fecha: {fecha or '-'} | Cédula: {documento or '-'}"
    pdf.drawString(40, height - 60, filtros)

    y = height - 90
    headers = ["Fecha", "Placa", "Movimiento", "Espacio", "Usuario", "Cédula", "Estado"]
    x_positions = [40, 160, 250, 340, 410, 510, 640]

    pdf.setFont("Helvetica-Bold", 9)
    for i, header in enumerate(headers):
        pdf.drawString(x_positions[i], y, header)

    y -= 18
    pdf.setFont("Helvetica", 8)

    for item in items:
        if y < 40:
            pdf.showPage()
            pdf.setFont("Helvetica-Bold", 9)
            for i, header in enumerate(headers):
                pdf.drawString(x_positions[i], height - 40, header)
            y = height - 58
            pdf.setFont("Helvetica", 8)

        values = [
            str(item.get("fecha_hora") or "")[:19],
            str(item.get("placa") or "")[:12],
            str(item.get("tipo_novedad") or "")[:12],
            str(item.get("espacio_numero") or "")[:10],
            str(item.get("username") or "")[:15],
            str(item.get("documento_usuario") or "")[:15],
            str(item.get("estado") or "")[:12],
        ]

        for i, value in enumerate(values):
            pdf.drawString(x_positions[i], y, value)

        y -= 14

    pdf.save()
    output.seek(0)

    filename = f"historial_accesos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    return send_file(
        output,
        as_attachment=True,
        download_name=filename,
        mimetype="application/pdf",
    )

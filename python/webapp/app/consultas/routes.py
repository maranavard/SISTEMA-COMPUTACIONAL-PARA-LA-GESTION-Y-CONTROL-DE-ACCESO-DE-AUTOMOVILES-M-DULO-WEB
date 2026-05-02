"""Rutas del módulo Consulta por Placa."""

import unicodedata

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.db import get_connection
from app.models.user import User
from app.models.vehiculo import Vehiculo
from app.utils.authz import community_required, normalize_role
from app.utils.field_validators import is_valid_cedula, is_valid_email


consultas_bp = Blueprint("consultas", __name__, url_prefix="/consultas")
INDEX_ROUTE = "consultas.index"
EDIT_ROUTE = "consultas.editar"


def _is_guard_role() -> bool:
    rol = normalize_role(getattr(current_user, "rol", ""))
    return rol in {"vigilante", "vigilancia", "seguridad_udec"}


def _normalize_lookup_text(value: str) -> str:
    text = " ".join((value or "").strip().lower().split())
    text = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in text if not unicodedata.combining(ch))


def _is_student_role(rol: str) -> bool:
    normalized = _normalize_lookup_text(rol)
    return normalized.startswith("estudiante")


def _build_user_lookup() -> dict[int, dict]:
    users = User.list_users()
    lookup = {}
    for user in users:
        raw_id = user.get("id")
        if raw_id is None:
            continue
        try:
            lookup[int(raw_id)] = user
        except (TypeError, ValueError):
            continue
    return lookup


def _ensure_vehicle_user_map_table() -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS public.vehiculo_usuario_map (
                    vehiculo_id INTEGER PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
                )
                """
            )
        conn.commit()


def _load_vehicle_user_map() -> dict[int, int]:
    _ensure_vehicle_user_map_table()
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT vehiculo_id, user_id FROM public.vehiculo_usuario_map")
            rows = cur.fetchall()

    mapping = {}
    for row in rows:
        try:
            mapping[int(row[0])] = int(row[1])
        except (TypeError, ValueError):
            continue
    return mapping


def _save_vehicle_user_map(vehiculo_id: int, user_id: int) -> None:
    _ensure_vehicle_user_map_table()
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO public.vehiculo_usuario_map (vehiculo_id, user_id, updated_at)
                VALUES (%s, %s, NOW())
                ON CONFLICT (vehiculo_id)
                DO UPDATE SET
                    user_id = EXCLUDED.user_id,
                    updated_at = NOW()
                """,
                (vehiculo_id, user_id),
            )
        conn.commit()


def _ensure_user_identification_column() -> None:
    """Garantiza una columna de identificación editable para usuarios."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = 'usuarios'
                  AND column_name IN ('numero_identificacion', 'identificacion', 'documento', 'cedula')
                LIMIT 1
                """
            )
            has_any = cur.fetchone()

            if not has_any:
                cur.execute("ALTER TABLE public.usuarios ADD COLUMN numero_identificacion VARCHAR(20)")
        conn.commit()


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

        if (
            needle == user_id
            or needle in username
            or needle in nombre
            or needle in apellido
            or needle in nombre_completo
            or needle in email
            or needle in documento
        ):
            return user_id

    raise ValueError("No se encontró el usuario indicado. Escribe un ID, usuario, correo o nombre válido.")


def _get_user_by_id(user_id: int) -> dict | None:
    lookup = _build_user_lookup()
    return lookup.get(user_id)


def _empty_user_data() -> dict:
    return {
        "usuario_nombre": "",
        "usuario_apellido": "",
        "usuario_nombre_completo": "",
        "usuario_username": "",
        "usuario_email": "",
        "usuario_identificacion": "",
        "usuario_estado": "",
        "usuario_rol": "",
        "usuario_activo_ok": False,
        "usuario_rol_ok": False,
        "usuario_email_ok": False,
        "usuario_cedula_ok": False,
        "perfil_validado_ok": False,
        "perfil_validado_msg": "Sin usuario asociado",
    }


def _resolve_user_from_item(item: dict, users_lookup: dict[int, dict]) -> dict | None:
    mapped_user_id = item.get("mapped_user_id")
    raw_user_id = mapped_user_id if mapped_user_id not in (None, "") else item.get("user_id")
    if raw_user_id in (None, ""):
        return None

    try:
        return users_lookup.get(int(raw_user_id))
    except (TypeError, ValueError):
        return None


def _build_user_status(nombre: str, apellido: str, email: str, identificacion: str, estado: str, rol: str) -> tuple[bool, bool, bool, bool, str]:
    activo_ok = _normalize_lookup_text(estado) == "activo"
    rol_ok = _is_student_role(rol)
    email_ok = bool(email) and is_valid_email(email)
    cedula_ok = bool(identificacion) and is_valid_cedula(identificacion)

    issues = []
    if not activo_ok:
        issues.append("Estado no activo")
    if not rol_ok:
        issues.append("Rol no estudiante")
    if not email_ok:
        issues.append("Correo inválido")
    if not cedula_ok:
        issues.append("Cédula inválida")

    message = "OK" if not issues else "; ".join(issues)
    return activo_ok, rol_ok, email_ok, cedula_ok, message


def _build_edit_payloads(form_data) -> tuple[str, str, str, dict, dict]:
    placa = Vehiculo.normalize_plate(form_data.get("placa", ""))
    tipo_vehiculo_id = (form_data.get("tipo_vehiculo_id", "") or "").strip()
    user_ref = form_data.get("user_id", "")

    vehicle_payload = {
        "placa": placa,
        "marca": (form_data.get("marca", "") or "").strip(),
        "modelo": (form_data.get("modelo", "") or "").strip(),
        "color": (form_data.get("color", "") or "").strip(),
        "tipo_vehiculo_id": tipo_vehiculo_id,
        "estado": (form_data.get("estado", "") or "").strip(),
    }

    user_payload = {
        "nombre": (form_data.get("user_nombre", "") or "").strip(),
        "apellido": (form_data.get("user_apellido", "") or "").strip(),
        "email": (form_data.get("user_email", "") or "").strip().lower(),
        "numero_identificacion": (form_data.get("user_numero_identificacion", "") or "").strip().replace(" ", ""),
        "estado": (form_data.get("user_estado", "") or "").strip(),
        "role": (form_data.get("user_role", "") or "").strip(),
    }

    return placa, tipo_vehiculo_id, user_ref, vehicle_payload, user_payload


def _validate_user_payload(user_payload: dict, email_message: str, cedula_message: str) -> str:
    if user_payload["email"] and not is_valid_email(user_payload["email"]):
        return email_message
    if user_payload["numero_identificacion"] and not is_valid_cedula(user_payload["numero_identificacion"]):
        return cedula_message
    return ""


def _resolve_related_user_id(user_ref: str, current_item: dict, item_id: int) -> str:
    if (user_ref or "").strip():
        return _resolve_user_id(user_ref)

    existing_user_id = str(current_item.get("user_id") or "").strip()
    if existing_user_id:
        return existing_user_id

    vehicle_user_map = _load_vehicle_user_map()
    return str(vehicle_user_map.get(item_id) or "").strip()


def _merge_user_payload_with_existing(user_payload: dict, existing_user: dict) -> dict:
    return {
        "nombre": user_payload["nombre"] or str(existing_user.get("nombre") or "").strip(),
        "apellido": user_payload["apellido"] or str(existing_user.get("apellido") or "").strip(),
        "email": user_payload["email"] or str(existing_user.get("email") or "").strip().lower(),
        "numero_identificacion": user_payload["numero_identificacion"]
        or str(existing_user.get("numero_identificacion") or "").strip().replace(" ", ""),
        "estado": user_payload["estado"] or str(existing_user.get("estado") or "").strip(),
        "role": user_payload["role"] or str(existing_user.get("rol") or "").strip(),
    }


def _enrich_item_with_user(item: dict, users_lookup: dict[int, dict]) -> dict:
    enriched = dict(item)
    user = _resolve_user_from_item(item=item, users_lookup=users_lookup)

    if not user:
        enriched.update(_empty_user_data())
        return enriched

    nombre = str(user.get("nombre") or "").strip()
    apellido = str(user.get("apellido") or "").strip()
    email = str(user.get("email") or "").strip()
    identificacion = str(user.get("numero_identificacion") or "").strip()
    estado = str(user.get("estado") or "").strip()
    rol = str(user.get("rol") or "").strip()
    username = str(user.get("username") or "").strip()

    activo_ok, rol_ok, email_ok, cedula_ok, status_message = _build_user_status(
        nombre=nombre,
        apellido=apellido,
        email=email,
        identificacion=identificacion,
        estado=estado,
        rol=rol,
    )

    enriched.update(
        {
            "usuario_nombre": nombre,
            "usuario_apellido": apellido,
            "usuario_nombre_completo": f"{nombre} {apellido}".strip(),
            "usuario_username": username,
            "usuario_email": email,
            "usuario_identificacion": identificacion,
            "usuario_estado": estado,
            "usuario_rol": rol,
            "usuario_activo_ok": activo_ok,
            "usuario_rol_ok": rol_ok,
            "usuario_email_ok": email_ok,
            "usuario_cedula_ok": cedula_ok,
            "perfil_validado_ok": status_message == "OK",
            "perfil_validado_msg": status_message,
        }
    )
    return enriched


def _attach_mapped_users(items: list[dict]) -> list[dict]:
    vehicle_user_map = _load_vehicle_user_map()
    for item in items:
        vehiculo_id = item.get("id")
        if vehiculo_id in (None, ""):
            item["mapped_user_id"] = None
            continue
        try:
            item["mapped_user_id"] = vehicle_user_map.get(int(vehiculo_id))
        except (TypeError, ValueError):
            item["mapped_user_id"] = None
    return items


def _filter_items_by_placa(items: list[dict], placa_filtro: str) -> list[dict]:
    if not placa_filtro:
        return items
    return [item for item in items if (item.get("placa") or "").upper().find(placa_filtro) >= 0]


def _filter_items_by_usuario(items: list[dict], usuario_filtro: str) -> list[dict]:
    if not usuario_filtro:
        return items

    needle = _normalize_lookup_text(usuario_filtro)
    return [
        item
        for item in items
        if needle in _normalize_lookup_text(item.get("usuario_nombre") or "")
        or needle in _normalize_lookup_text(item.get("usuario_apellido") or "")
        or needle in _normalize_lookup_text(item.get("usuario_nombre_completo") or "")
        or needle in _normalize_lookup_text(item.get("usuario_username") or "")
        or needle in _normalize_lookup_text(item.get("usuario_email") or "")
    ]


def _filter_items_by_cedula(items: list[dict], cedula_filtro: str) -> list[dict]:
    if not cedula_filtro:
        return items
    needle = _normalize_lookup_text(cedula_filtro)
    return [item for item in items if needle in _normalize_lookup_text(item.get("usuario_identificacion") or "")]


def _resolve_associated_user(item: dict, user_lookup: dict[int, dict], item_id: int) -> dict | None:
    raw_user_id = item.get("user_id")
    if raw_user_id in (None, ""):
        vehicle_user_map = _load_vehicle_user_map()
        raw_user_id = vehicle_user_map.get(item_id)
    if raw_user_id in (None, ""):
        return None
    try:
        return user_lookup.get(int(raw_user_id))
    except (TypeError, ValueError):
        return None


def _update_associated_user_if_needed(resolved_user_id: str, user_fields_started: bool, user_payload: dict, item_id: int) -> str:
    if not (resolved_user_id and user_fields_started):
        return ""

    _ensure_user_identification_column()

    existing_user = _get_user_by_id(int(resolved_user_id))
    if not existing_user:
        return "No se encontró el usuario asociado para completar los datos faltantes."

    merged_user_payload = _merge_user_payload_with_existing(user_payload=user_payload, existing_user=existing_user)
    merged_user_error = _validate_user_payload(
        user_payload=merged_user_payload,
        email_message="El correo final del usuario es inválido. Corrígelo para guardar.",
        cedula_message="La cédula final del usuario es inválida. Corrígela para guardar.",
    )
    if merged_user_error:
        return merged_user_error

    User.update_user(
        user_id=int(resolved_user_id),
        role=merged_user_payload["role"],
        estado=merged_user_payload["estado"],
        nombre=merged_user_payload["nombre"],
        apellido=merged_user_payload["apellido"],
        email=merged_user_payload["email"],
        numero_identificacion=merged_user_payload["numero_identificacion"],
    )
    return ""


@consultas_bp.get("/")
@login_required
@community_required
def index():
    placa_filtro = (request.args.get("placa", "") or "").strip().upper()
    usuario_filtro = (request.args.get("usuario", "") or "").strip()
    cedula_filtro = (request.args.get("cedula", "") or "").strip()

    items = _attach_mapped_users(Vehiculo.list_items())
    users_lookup = _build_user_lookup()
    items = [_enrich_item_with_user(item=item, users_lookup=users_lookup) for item in items]
    items = _filter_items_by_placa(items=items, placa_filtro=placa_filtro)
    items = _filter_items_by_usuario(items=items, usuario_filtro=usuario_filtro)
    items = _filter_items_by_cedula(items=items, cedula_filtro=cedula_filtro)

    return render_template(
        "consultas/index.html",
        items=items,
        placa_filtro=placa_filtro,
        usuario_filtro=usuario_filtro,
        cedula_filtro=cedula_filtro,
        is_guard_role=_is_guard_role(),
    )


@consultas_bp.get("/<int:item_id>")
@login_required
@community_required
def visualizar(item_id: int):
    item = Vehiculo.get_by_id(item_id)
    if not item:
        flash("No se encontró el vehículo solicitado.", "error")
        return redirect(url_for(INDEX_ROUTE))

    return render_template("consultas/view.html", item=item)


@consultas_bp.get("/<int:item_id>/editar")
@login_required
@community_required
def editar(item_id: int):
    if _is_guard_role():
        flash("El perfil vigilante solo puede consultar información básica por placa.", "error")
        return redirect(url_for(INDEX_ROUTE))

    item = Vehiculo.get_by_id(item_id)
    if not item:
        flash("No se encontró el vehículo para editar.", "error")
        return redirect(url_for(INDEX_ROUTE))

    tipos_vehiculo = Vehiculo.list_vehicle_types()
    user_lookup = _build_user_lookup()
    usuario_asociado = _resolve_associated_user(item=item, user_lookup=user_lookup, item_id=item_id)

    editable_roles = [
        "estudiante_udec",
        "docente_udec",
        "funcionario_area",
        "vigilante",
        "admin_sistema",
        "administrador",
    ]

    return render_template(
        "consultas/edit.html",
        item=item,
        tipos_vehiculo=tipos_vehiculo,
        usuario_asociado=usuario_asociado,
        editable_roles=editable_roles,
    )


@consultas_bp.post("/<int:item_id>/editar")
@login_required
@community_required
def guardar_edicion(item_id: int):
    if _is_guard_role():
        flash("El perfil vigilante no puede editar información vehicular.", "error")
        return redirect(url_for(INDEX_ROUTE))

    current_item = Vehiculo.get_by_id(item_id)
    if not current_item:
        flash("No se encontró el vehículo para editar.", "error")
        return redirect(url_for(INDEX_ROUTE))

    placa, tipo_vehiculo_id, user_ref, payload, user_payload = _build_edit_payloads(request.form)

    plate_ok, plate_error = Vehiculo.validate_plate_format(placa=placa, tipo_vehiculo_id=tipo_vehiculo_id)
    if not plate_ok:
        flash(plate_error, "error")
        return redirect(url_for(EDIT_ROUTE, item_id=item_id))

    user_payload_error = _validate_user_payload(
        user_payload=user_payload,
        email_message="Formato de correo inválido. Usa un correo válido (ej: usuario@dominio.com).",
        cedula_message="Formato de cédula inválido. Debe contener solo números (6 a 12 dígitos).",
    )
    if user_payload_error:
        flash(user_payload_error, "error")
        return redirect(url_for(EDIT_ROUTE, item_id=item_id))

    user_fields_started = any(user_payload.values())

    try:
        resolved_user_id = _resolve_related_user_id(user_ref=user_ref, current_item=current_item, item_id=item_id)

        if user_fields_started and not resolved_user_id:
            flash("Para editar datos del usuario debes indicar un usuario asociado válido.", "error")
            return redirect(url_for(EDIT_ROUTE, item_id=item_id))

        if resolved_user_id:
            payload["user_id"] = resolved_user_id

        Vehiculo.update_item(item_id=item_id, data=payload)

        if resolved_user_id:
            _save_vehicle_user_map(vehiculo_id=item_id, user_id=int(resolved_user_id))

        user_update_error = _update_associated_user_if_needed(
            resolved_user_id=resolved_user_id,
            user_fields_started=user_fields_started,
            user_payload=user_payload,
            item_id=item_id,
        )
        if user_update_error:
            flash(user_update_error, "error")
            return redirect(url_for(EDIT_ROUTE, item_id=item_id))

        flash("Vehículo y datos de usuario actualizados correctamente.", "success")
    except ValueError as exc:
        flash(str(exc), "error")
    except Exception as exc:
        flash(f"No se pudo actualizar la información: {exc}", "error")

    return redirect(url_for(INDEX_ROUTE))


@consultas_bp.post("/<int:item_id>/borrar")
@login_required
@community_required
def borrar(item_id: int):
    if _is_guard_role():
        flash("El perfil vigilante no puede eliminar información vehicular.", "error")
        return redirect(url_for(INDEX_ROUTE))

    try:
        Vehiculo.delete_item(item_id)
        flash("Vehículo eliminado correctamente.", "success")
    except Exception as exc:
        flash(f"No se pudo eliminar el vehículo: {exc}", "error")

    return redirect(url_for(INDEX_ROUTE))

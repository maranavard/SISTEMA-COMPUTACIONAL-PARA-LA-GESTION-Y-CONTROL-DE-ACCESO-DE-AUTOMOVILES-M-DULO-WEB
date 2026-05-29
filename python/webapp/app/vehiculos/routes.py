@vehiculos_bp.get("/")
@login_required
@community_required
def list_items():
    can_manage_sensitive = _can_manage_sensitive()
    is_funcionario = _is_funcionario_role()
    placa_consulta = (request.args.get("placa", "") or "").strip().upper()
    vehiculo_consulta = None

    try:
        tipos_vehiculo = Vehiculo.list_vehicle_types()
    except Exception as exc:
        tipos_vehiculo = []
        flash(f"No se pudieron cargar los tipos de vehículo: {exc}", "warning")

    conductores = []
    usuarios = []
    items = []

    try:
        if is_funcionario and not can_manage_sensitive:
            own_conductor = None
            try:
                own_conductor = Conductor.get_by_user_id(int(current_user.id))
            except Exception as exc:
                flash(f"No se pudo cargar tu perfil de conductor: {exc}", "warning")

            conductores = [own_conductor] if own_conductor else []
            items = Vehiculo.list_items_by_user_id(int(current_user.id))
        else:
            try:
                conductores = Conductor.list_items()
            except Exception as exc:
                conductores = []
                flash(f"No se pudieron cargar los conductores: {exc}", "warning")

            try:
                usuarios = User.list_users()
            except Exception as exc:
                usuarios = []
                flash(f"No se pudieron cargar los usuarios: {exc}", "warning")

            items = Vehiculo.list_items()
    except Exception as exc:
        flash(f"No se pudo cargar la información de vehículos: {exc}", "error")
        items = []

    warning_items = []
    error_items = []

    # Carga documental liviana: no consultar documento por documento para evitar timeout.
    for item in items:
        item["fecha_vencimiento_soat_input"] = ""
        item["fecha_vencimiento_tecnomecanica_input"] = ""
        item["fecha_vencimiento_tarjeta_propiedad_input"] = ""
        item["doc_status_level"] = "success"
        item["doc_status_message"] = "Consulta documental disponible al actualizar o consultar por placa."
        item["conductor_ref"] = str(item.get("conductor_id") or "")
        item["user_ref"] = str(item.get("user_id") or "")

    if placa_consulta:
        try:
            vehiculo_consulta = Vehiculo.get_by_placa(placa_consulta)
        except Exception as exc:
            vehiculo_consulta = None
            flash(f"No se pudo consultar la placa indicada: {exc}", "warning")

    doc_status_consulta = None
    if can_manage_sensitive and vehiculo_consulta and vehiculo_consulta.get("id"):
        try:
            doc_status_consulta = DocumentoVehiculo.get_status_summary(
                int(vehiculo_consulta.get("id")),
                warning_days=30,
            )
        except Exception:
            doc_status_consulta = None

    return render_template(
        "vehiculos/index.html",
        placa_consulta=placa_consulta,
        vehiculo_consulta=vehiculo_consulta,
        doc_status_consulta=doc_status_consulta,
        items=items,
        warning_items=warning_items,
        error_items=error_items,
        can_manage_sensitive=can_manage_sensitive,
        is_funcionario=is_funcionario,
        tipos_vehiculo=tipos_vehiculo,
        conductores=conductores,
        usuarios=usuarios,
    )

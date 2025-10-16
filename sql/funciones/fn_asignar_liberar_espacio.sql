CREATE OR REPLACE FUNCTION public.fn_asignar_liberar_espacio()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    v_tipo integer;
    v_espacio_id integer;
BEGIN
    -- Solo actuamos en ingresos o salidas
    IF NEW.tipo_novedad IS NULL THEN
        RETURN NEW;
    END IF;

    IF lower(NEW.tipo_novedad) = 'ingreso' THEN
        -- Obtener tipo de vehiculo del id_vehiculo enviado
        SELECT tipo_vehiculo_id
        INTO v_tipo
        FROM public.vehiculos
        WHERE id = NEW.id_vehiculo
        LIMIT 1;

        -- Si no encontramos tipo, dejamos pendiente
        IF v_tipo IS NULL THEN
            NEW.id_espacio := NULL;
            NEW.estado := COALESCE(NEW.estado, 'pendiente');
            RETURN NEW;
        END IF;

        -- Buscar un espacio libre del tipo correspondiente
        SELECT id_espacio
        INTO v_espacio_id
        FROM public.espacio
        WHERE tipo_vehiculo_id = v_tipo
          AND estado = 'libre'
        ORDER BY numero
        FOR UPDATE SKIP LOCKED
        LIMIT 1;

        IF v_espacio_id IS NOT NULL THEN
            -- marcar espacio como ocupado
            UPDATE public.espacio
            SET estado = 'ocupado'
            WHERE id_espacio = v_espacio_id;

            NEW.id_espacio := v_espacio_id;
            NEW.estado := 'registrado'; -- ya asignado
        ELSE
            -- No hay espacio libre: dejamos pendiente
            NEW.id_espacio := NULL;
            NEW.estado := 'pendiente';
        END IF;

        RETURN NEW;
    ELSIF lower(NEW.tipo_novedad) = 'salida' THEN
        -- Si no nos dieron id_espacio, intentar recuperarlo del último ingreso registrado
        IF NEW.id_espacio IS NULL THEN
            SELECT id_espacio
            INTO v_espacio_id
            FROM public.novedad
            WHERE id_vehiculo = NEW.id_vehiculo
              AND lower(tipo_novedad) = 'ingreso'
              AND estado = 'registrado'
            ORDER BY fecha_hora DESC
            LIMIT 1;
        ELSE
            v_espacio_id := NEW.id_espacio;
        END IF;

        IF v_espacio_id IS NOT NULL THEN
            -- liberar espacio
            UPDATE public.espacio
            SET estado = 'libre'
            WHERE id_espacio = v_espacio_id;
            NEW.id_espacio := v_espacio_id;
            NEW.estado := COALESCE(NEW.estado, 'registrado');
        ELSE
            -- no se encontró espacio asociado; mantener info
            NEW.id_espacio := NULL;
            NEW.estado := COALESCE(NEW.estado, 'registrado');
        END IF;

        RETURN NEW;
    ELSE
        -- Otros tipos de novedad: no tocar espacios
        RETURN NEW;
    END IF;
END;
$$;

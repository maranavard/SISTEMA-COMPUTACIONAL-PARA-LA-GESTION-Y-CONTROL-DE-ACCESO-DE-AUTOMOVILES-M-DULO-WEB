-- 007_fix_novedad_triggers_and_functions.sql
-- Corrige inconsistencias en funciones de asignación/liberación y evita conflicto de triggers en novedad.

BEGIN;

-- 1) Función canónica para asignar/liberar espacio desde INSERT en novedad
CREATE OR REPLACE FUNCTION public.fn_asignar_liberar_espacio()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    v_tipo INTEGER;
    v_espacio_id INTEGER;
BEGIN
    IF NEW.tipo_novedad IS NULL THEN
        RETURN NEW;
    END IF;

    IF lower(NEW.tipo_novedad) = 'ingreso' THEN
        SELECT tipo_vehiculo_id
        INTO v_tipo
        FROM public.vehiculos
        WHERE id = NEW.id_vehiculo
        LIMIT 1;

        IF v_tipo IS NULL THEN
            NEW.id_espacio := NULL;
            NEW.estado := COALESCE(NEW.estado, 'pendiente');
            RETURN NEW;
        END IF;

        SELECT id_espacio
        INTO v_espacio_id
        FROM public.espacio
        WHERE tipo_vehiculo_id = v_tipo
          AND estado = 'libre'
        ORDER BY numero
        FOR UPDATE SKIP LOCKED
        LIMIT 1;

        IF v_espacio_id IS NOT NULL THEN
            UPDATE public.espacio
            SET estado = 'ocupado'
            WHERE id_espacio = v_espacio_id;

            NEW.id_espacio := v_espacio_id;
            NEW.estado := 'registrado';
        ELSE
            NEW.id_espacio := NULL;
            NEW.estado := 'pendiente';
        END IF;

        RETURN NEW;
    ELSIF lower(NEW.tipo_novedad) = 'salida' THEN
        IF NEW.id_espacio IS NULL THEN
            SELECT id_espacio
            INTO v_espacio_id
            FROM public.novedad
            WHERE id_vehiculo = NEW.id_vehiculo
              AND lower(tipo_novedad) = 'ingreso'
              AND estado = 'registrado'
              AND id_espacio IS NOT NULL
            ORDER BY fecha_hora DESC
            LIMIT 1;
        ELSE
            v_espacio_id := NEW.id_espacio;
        END IF;

        IF v_espacio_id IS NOT NULL THEN
            UPDATE public.espacio
            SET estado = 'libre'
            WHERE id_espacio = v_espacio_id;

            NEW.id_espacio := v_espacio_id;
            NEW.estado := COALESCE(NEW.estado, 'finalizado');
        ELSE
            NEW.id_espacio := NULL;
            NEW.estado := COALESCE(NEW.estado, 'pendiente');
        END IF;

        RETURN NEW;
    ELSE
        RETURN NEW;
    END IF;
END;
$$;

-- 2) Función de ingreso por placa (versión corregida)
CREATE OR REPLACE FUNCTION public.assign_space_and_register_ingreso(
    p_placa character varying,
    p_user_id integer
)
RETURNS TABLE(assigned_space_id integer, assigned_space_num character varying)
LANGUAGE plpgsql
AS $$
DECLARE
    v_vehicle_id INT;
    v_tipo_id INT;
    v_space_id INT;
    v_space_num VARCHAR;
BEGIN
    SELECT id, tipo_vehiculo_id
    INTO v_vehicle_id, v_tipo_id
    FROM public.vehiculos
    WHERE placa = p_placa
    LIMIT 1;

    IF v_vehicle_id IS NULL THEN
        RAISE EXCEPTION 'El vehículo con placa % no existe en el sistema', p_placa;
    END IF;

    SELECT id_espacio, numero
    INTO v_space_id, v_space_num
    FROM public.espacio
    WHERE estado = 'libre'
      AND (tipo_vehiculo_id = v_tipo_id OR tipo_vehiculo_id IS NULL)
    ORDER BY id_espacio
    LIMIT 1;

    IF v_space_id IS NULL THEN
        RAISE NOTICE 'No hay espacios libres compatibles para el vehículo %', p_placa;
        RETURN QUERY SELECT NULL::INT, NULL::VARCHAR;
        RETURN;
    END IF;

    UPDATE public.espacio
    SET estado = 'ocupado'
    WHERE id_espacio = v_space_id;

    INSERT INTO public.novedad (
        tipo_novedad,
        id_vehiculo,
        fecha_hora,
        id_usuario,
        id_espacio,
        observaciones,
        estado
    )
    VALUES (
        'ingreso',
        v_vehicle_id,
        NOW(),
        p_user_id,
        v_space_id,
        'Ingreso automático',
        'registrado'
    );

    RETURN QUERY SELECT v_space_id, v_space_num;
END;
$$;

-- 3) Desactivar función legacy para evitar doble manejo de espacios
DROP FUNCTION IF EXISTS public.fn_novedad_space_manage();

-- 4) Dejar un solo trigger BEFORE INSERT para asignar/liberar
DROP TRIGGER IF EXISTS trg_novedad_asignacion ON public.novedad;
DROP TRIGGER IF EXISTS trg_novedad_space_manage ON public.novedad;
DROP TRIGGER IF EXISTS trg_novedad_space ON public.novedad;
DROP TRIGGER IF EXISTS trg_novedad_space_before_insert ON public.novedad;

CREATE TRIGGER trg_novedad_asignacion
BEFORE INSERT ON public.novedad
FOR EACH ROW
EXECUTE FUNCTION public.fn_asignar_liberar_espacio();

-- 5) Asegurar trigger de auditoría
DROP TRIGGER IF EXISTS trg_audit_novedades ON public.novedad;
CREATE TRIGGER trg_audit_novedades
AFTER INSERT OR UPDATE ON public.novedad
FOR EACH ROW
EXECUTE FUNCTION public.fn_audit_novedades();

COMMIT;
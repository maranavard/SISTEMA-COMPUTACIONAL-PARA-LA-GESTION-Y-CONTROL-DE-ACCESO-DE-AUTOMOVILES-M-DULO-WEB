-- FUNCTION: public.assign_space_and_register_ingreso(character varying, integer)

-- DROP FUNCTION IF EXISTS public.assign_space_and_register_ingreso(character varying, integer);

CREATE OR REPLACE FUNCTION public.assign_space_and_register_ingreso(
	p_placa character varying,
	p_user_id integer)
    RETURNS TABLE(assigned_space_id integer, assigned_space_num character varying) 
    LANGUAGE 'plpgsql'
    COST 100
    VOLATILE PARALLEL UNSAFE
    ROWS 1000

AS $BODY$
DECLARE
  v_vehicle_id INT;
  v_tipo_id INT;
  v_space_id INT;
  v_space_num VARCHAR;
BEGIN
  -- 1. Obtener id y tipo del vehículo
  SELECT id, tipo_vehiculo_id
  INTO v_vehicle_id, v_tipo_id
  FROM public.vehiculos
  WHERE placa = p_placa
  LIMIT 1;

  IF v_vehicle_id IS NULL THEN
    RAISE EXCEPTION 'El vehículo con placa % no existe en el sistema', p_placa;
  END IF;

  -- 2. Buscar espacio libre compatible con el tipo de vehículo
  SELECT id_espacio, numero
  INTO v_space_id, v_space_num
  FROM public.espacio
  WHERE estado = 'libre'
    AND (tipo_vehiculo_id = v_tipo_id OR tipo_vehiculo_id IS NULL)
  ORDER BY id
  LIMIT 1;

  IF v_space_id IS NULL THEN
    RAISE NOTICE 'No hay espacios libres compatibles para el vehículo %', p_placa;
    RETURN QUERY SELECT NULL::INT, NULL::VARCHAR;
    RETURN;
  END IF;

  -- 3. Marcar espacio como ocupado
  UPDATE public.espacio
  SET estado = 'ocupado'
  WHERE id_espacio = v_space_id;

  -- 4. Registrar novedad de ingreso
  INSERT INTO public.novedad (
      tipo_novedad,
      id_vehiculo,
      fecha_hora,
      id_usuario,
      id_espacio,
      observaciones
  )
  VALUES (
      'ingreso',
      v_vehicle_id,
      NOW(),
      p_user_id,
      v_space_id,
      'Ingreso automático'
  );

  -- 5. Devolver datos del espacio asignado
  RETURN QUERY SELECT v_space_id, v_space_num;
END;
$BODY$;

ALTER FUNCTION public.assign_space_and_register_ingreso(character varying, integer)
    OWNER TO postgres;

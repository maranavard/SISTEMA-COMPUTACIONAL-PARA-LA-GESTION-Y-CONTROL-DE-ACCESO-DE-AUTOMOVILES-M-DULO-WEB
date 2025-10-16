-- FUNCTION: public.assign_parking_space_for_plate(character varying)

-- DROP FUNCTION IF EXISTS public.assign_parking_space_for_plate(character varying);

CREATE OR REPLACE FUNCTION public.assign_parking_space_for_plate(
	p_plate character varying)
    RETURNS integer
    LANGUAGE 'plpgsql'
    COST 100
    VOLATILE PARALLEL UNSAFE
AS $BODY$
DECLARE
  v_vehicle_type VARCHAR(20);
  v_space_id INT;
BEGIN
  -- obtener tipo de vehiculo desde plates (por defecto 'car' si no hay dato)
  SELECT COALESCE(tipo_vehiculo,'car') INTO v_vehicle_type FROM public.plates WHERE placa = p_plate LIMIT 1;

  -- encontrar espacio disponible que acepte el tipo (o 'all')
  SELECT id_espacio INTO v_space_id
  FROM public.parking_spaces
  WHERE is_available = TRUE
    AND (vehicle_type = v_vehicle_type OR vehicle_type = 'all')
  ORDER BY id
  LIMIT 1;

  IF v_space_id IS NULL THEN
    RETURN NULL; -- no hay espacio disponible
  END IF;

  -- crear asignación (histórico)
  INSERT INTO public.space_assignments (plate_number, space_id, assigned_at)
  VALUES (p_plate, v_space_id, NOW());

  -- marcar espacio como no disponible
  UPDATE public.parking_spaces SET is_available = FALSE WHERE id = v_space_id;

  RETURN v_space_id;
END;
$BODY$;

ALTER FUNCTION public.assign_parking_space_for_plate(character varying)
    OWNER TO postgres;

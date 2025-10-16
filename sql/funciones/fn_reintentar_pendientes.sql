CREATE OR REPLACE FUNCTION public.fn_reintentar_pendientes()
RETURNS VOID LANGUAGE plpgsql AS $$
DECLARE
  r RECORD;
  v_tipo INTEGER;
  v_esp INTEGER;
BEGIN
  FOR r IN SELECT * FROM public.novedad WHERE estado = 'pendiente' ORDER BY fecha_hora
  LOOP
    IF r.id_vehiculo IS NOT NULL THEN
      SELECT tipo_vehiculo_id INTO v_tipo FROM public.vehiculos WHERE id = r.id_vehiculo LIMIT 1;
    ELSE
      v_tipo := NULL;
    END IF;

    IF v_tipo IS NOT NULL THEN
      SELECT id_espacio INTO v_esp
      FROM public.espacio
      WHERE tipo_vehiculo_id = v_tipo AND estado = 'libre'
      ORDER BY numero
      LIMIT 1
      FOR UPDATE SKIP LOCKED;

      IF v_esp IS NOT NULL THEN
        UPDATE public.espacio SET estado = 'ocupado' WHERE id_espacio = v_esp;
        UPDATE public.novedad SET id_espacio = v_esp, estado = 'registrado' WHERE id = r.id;
      END IF;
    END IF;
  END LOOP;
END;
$$;

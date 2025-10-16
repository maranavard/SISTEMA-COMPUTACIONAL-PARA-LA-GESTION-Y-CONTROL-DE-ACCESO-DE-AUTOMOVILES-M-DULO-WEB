-- test_salida.sql
-- Inserta una salida de prueba y muestra resultados

BEGIN;

WITH ids AS (
  SELECT (SELECT id FROM public.vehiculos LIMIT 1) AS id_vehiculo,
         (SELECT id FROM public.usuarios LIMIT 1) AS id_usuario
)
INSERT INTO public.novedad (tipo_novedad, id_vehiculo, id_usuario, observaciones)
SELECT 'salida', id_vehiculo, id_usuario, 'test_salida' FROM ids
RETURNING *;

COMMIT;

SELECT * FROM public.novedad ORDER BY fecha_hora DESC LIMIT 5;
SELECT id_espacio, numero, estado FROM public.espacio ORDER BY numero LIMIT 10;

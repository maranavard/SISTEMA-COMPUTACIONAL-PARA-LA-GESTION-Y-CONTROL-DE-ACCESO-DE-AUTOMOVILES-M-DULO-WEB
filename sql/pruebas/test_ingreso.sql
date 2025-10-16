-- test_ingreso.sql
-- Inserta un ingreso de prueba y muestra resultados

BEGIN;

-- seleccionar ids de ejemplo (ajusta si quieres ids concretos)
WITH ids AS (
  SELECT (SELECT id FROM public.vehiculos LIMIT 1) AS id_vehiculo,
         (SELECT id FROM public.usuarios LIMIT 1) AS id_usuario
)
INSERT INTO public.novedad (tipo_novedad, id_vehiculo, id_usuario, observaciones)
SELECT 'ingreso', id_vehiculo, id_usuario, 'test_ingreso' FROM ids
RETURNING *;

COMMIT;

-- Verificar últimas novedades y estado de espacios
SELECT * FROM public.novedad ORDER BY fecha_hora DESC LIMIT 5;
SELECT id_espacio, numero, estado FROM public.espacio ORDER BY numero LIMIT 10;

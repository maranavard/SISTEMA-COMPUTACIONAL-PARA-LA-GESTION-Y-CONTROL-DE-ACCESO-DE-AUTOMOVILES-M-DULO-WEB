-- test_pendientes.sql
-- Forzar todos ocupados, insertar ingreso que quede pendiente, liberar 1 y ejecutar reintento

BEGIN;
-- Forzar ocupación de espacios del tipo 'auto' (ajusta nombre si tu tipo cambia)
UPDATE public.espacio
SET estado = 'ocupado'
WHERE tipo_vehiculo_id = (SELECT id FROM public.tipo_vehiculo WHERE nombre = 'auto' LIMIT 1);

-- Insertar novedad que deberá quedar pendiente
INSERT INTO public.novedad (tipo_novedad, id_vehiculo, id_usuario, observaciones)
VALUES (
  'ingreso',
  (SELECT id FROM public.vehiculos WHERE tipo_vehiculo_id = (SELECT id FROM public.tipo_vehiculo WHERE nombre = 'auto' LIMIT 1) LIMIT 1),
  (SELECT id FROM public.usuarios LIMIT 1),
  'test_pendiente'
)
RETURNING *;

COMMIT;

-- Ver novedad pendiente
SELECT * FROM public.novedad WHERE estado='pendiente' ORDER BY fecha_hora DESC LIMIT 10;

-- Liberar 1 espacio del tipo
WITH one AS (
  SELECT id_espacio FROM public.espacio WHERE tipo_vehiculo_id = (SELECT id FROM public.tipo_vehiculo WHERE nombre='auto' LIMIT 1) LIMIT 1
)
UPDATE public.espacio SET estado='libre' WHERE id_espacio IN (SELECT id_espacio FROM one);

-- Ejecutar reintento manualmente
SELECT public.fn_reintentar_pendientes();

-- Verificar resultados
SELECT * FROM public.novedad WHERE estado IN ('pendiente','registrado') ORDER BY fecha_hora DESC LIMIT 10;
SELECT id_espacio, numero, estado FROM public.espacio ORDER BY numero LIMIT 20;

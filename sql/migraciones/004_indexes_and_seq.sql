-- 004_indexes_and_seq.sql
BEGIN;

-- Índices recomendados si no existen
CREATE INDEX IF NOT EXISTS idx_espacio_estado_tipo ON public.espacio (estado, tipo_vehiculo_id);
CREATE INDEX IF NOT EXISTS idx_novedad_vehiculo_fecha ON public.novedad (id_vehiculo, fecha_hora);
CREATE INDEX IF NOT EXISTS idx_vehiculos_placa ON public.vehiculos (placa);

-- Sincronizar secuencias para tablas con serials (ejecuta por si acaso)
SELECT setval(pg_get_serial_sequence('public.vehiculos','id'), COALESCE((SELECT MAX(id) FROM public.vehiculos),0));
SELECT setval(pg_get_serial_sequence('public.novedad','id'), COALESCE((SELECT MAX(id) FROM public.novedad),0));
SELECT setval(pg_get_serial_sequence('public.espacio','id_espacio'), COALESCE((SELECT MAX(id_espacio) FROM public.espacio),0));

COMMIT;

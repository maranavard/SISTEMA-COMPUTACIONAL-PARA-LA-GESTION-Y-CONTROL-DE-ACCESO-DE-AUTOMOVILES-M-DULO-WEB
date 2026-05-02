-- 00_verificacion_bd_sprint1.sql
-- Ejecutar en la BD: sistema_control

DROP TABLE IF EXISTS tmp_verif_const;
CREATE TEMP TABLE tmp_verif_const AS
SELECT
  'public'::text AS schema_name,
  'novedad'::text AS novedad_table,
  'salida'::text AS tipo_salida,
  'pendiente'::text AS estado_pendiente;

-- 1) Verificar tablas críticas del MVP
SELECT table_name
FROM information_schema.tables t
JOIN tmp_verif_const c ON c.schema_name = t.table_schema
WHERE table_schema = c.schema_name
  AND table_name IN (
    'roles','usuarios','conductors','conductores','vehiculos','espacio',c.novedad_table,
    'registro_visitantes','visitantes','documentos','tipo_doc','tipo_documento',
    'novedades_audit','asignaciones_log'
  )
ORDER BY table_name;

-- 2) Revisar estructura de usuarios/roles
SELECT column_name, data_type
FROM information_schema.columns ic
JOIN tmp_verif_const c ON c.schema_name = ic.table_schema
WHERE table_schema = c.schema_name
  AND table_name IN ('usuarios','roles')
ORDER BY table_name, ordinal_position;

-- 3) Verificar índices y constraints sobre placa
SELECT conname AS constraint_name, pg_get_constraintdef(c.oid) AS definition
FROM pg_constraint c
JOIN pg_class t ON c.conrelid = t.oid
JOIN pg_namespace n ON n.oid = t.relnamespace
JOIN tmp_verif_const k ON TRUE
WHERE n.nspname = k.schema_name
  AND t.relname = 'vehiculos'
  AND pg_get_constraintdef(c.oid) ILIKE '%placa%';

-- 4) Estado actual de espacios
SELECT estado, COUNT(*) AS total
FROM public.espacio
GROUP BY estado
ORDER BY estado;

-- 5) Tipos de vehículo y cupos por tipo
SELECT tv.nombre AS tipo_vehiculo, e.estado, COUNT(*) AS total
FROM public.espacio e
LEFT JOIN public.tipo_vehiculo tv ON tv.id = e.tipo_vehiculo_id
GROUP BY tv.nombre, e.estado
ORDER BY tv.nombre, e.estado;

-- 6) Trigger activo en novedad
SELECT trigger_name, event_manipulation, event_object_table, action_statement
FROM information_schema.triggers t
JOIN tmp_verif_const c ON TRUE
WHERE event_object_schema = c.schema_name
  AND event_object_table = c.novedad_table;

-- 7) Últimos movimientos de novedad
SELECT id, tipo_novedad, id_vehiculo, id_espacio, estado, fecha_hora
FROM public.novedad
ORDER BY id DESC
LIMIT 15;

-- 8) Resumen de pendientes por tipo de novedad
SELECT lower(tipo_novedad) AS tipo_novedad, estado, COUNT(*) AS total
FROM public.novedad
GROUP BY lower(tipo_novedad), estado
ORDER BY lower(tipo_novedad), estado;

-- 9) Salidas pendientes sin espacio asociado (caso crítico)
SELECT id, id_vehiculo, id_espacio, estado, fecha_hora
FROM public.novedad
WHERE lower(tipo_novedad) = 'salida'
  AND estado = 'pendiente'
ORDER BY fecha_hora DESC
LIMIT 30;

-- 10) Triggers reales activos en public.novedad (fuente técnica)
SELECT
  t.tgname AS trigger_name,
  p.proname AS function_name,
  pg_get_triggerdef(t.oid) AS trigger_def
FROM pg_trigger t
JOIN pg_class c ON c.oid = t.tgrelid
JOIN pg_namespace n ON n.oid = c.relnamespace
JOIN pg_proc p ON p.oid = t.tgfoid
JOIN tmp_verif_const k ON TRUE
WHERE n.nspname = k.schema_name
  AND c.relname = k.novedad_table
  AND NOT t.tgisinternal
ORDER BY t.tgname;

-- 11) Código fuente de funciones clave de asignación/liberación
SELECT p.proname AS function_name,
       pg_get_functiondef(p.oid) AS function_definition
FROM pg_proc p
JOIN pg_namespace n ON n.oid = p.pronamespace
JOIN tmp_verif_const k ON TRUE
WHERE n.nspname = k.schema_name
  AND p.proname IN ('fn_asignar_liberar_espacio', 'fn_novedad_space_manage', 'assign_space_and_register_ingreso');

DROP TABLE IF EXISTS tmp_verif_const;

-- 01_regresion_ingreso_salida.sql
-- Ejecutar después de 007_fix_novedad_triggers_and_functions.sql
-- Modo automático: toma una placa y usuario existentes para la prueba.

-- 0) Crear parámetros automáticos de prueba
SET client_min_messages TO WARNING;
DROP TABLE IF EXISTS tmp_regresion_params;
RESET client_min_messages;

CREATE TEMP TABLE tmp_regresion_params AS
SELECT
    v.placa::varchar AS placa,
    u.id::int AS user_id,
	v.id::int AS vehiculo_id,
	v.tipo_vehiculo_id
FROM public.vehiculos v
CROSS JOIN LATERAL (
    SELECT id
    FROM public.usuarios
    ORDER BY id
    LIMIT 1
) u
WHERE EXISTS (
	SELECT 1
	FROM public.espacio e
	WHERE e.estado = 'libre'
	  AND (e.tipo_vehiculo_id = v.tipo_vehiculo_id OR e.tipo_vehiculo_id IS NULL)
)
ORDER BY v.id DESC
LIMIT 1;

-- Si no hay datos base, este SELECT quedará vacío y debes crear al menos 1 usuario y 1 vehículo.
SELECT * FROM tmp_regresion_params;

-- Diagnóstico rápido cuando no hay fila en tmp_regresion_params
SELECT
	(SELECT COUNT(*) FROM public.usuarios) AS total_usuarios,
	(SELECT COUNT(*) FROM public.vehiculos) AS total_vehiculos,
	(SELECT COUNT(*) FROM public.espacio WHERE estado = 'libre') AS espacios_libres_total;

-- 1) Ingreso automático por placa
SELECT *
FROM tmp_regresion_params p,
LATERAL public.assign_space_and_register_ingreso(p.placa, p.user_id);

-- 2) Revisar último ingreso para esa misma placa
SELECT n.id, n.tipo_novedad, n.id_vehiculo, n.id_espacio, n.estado, n.fecha_hora
FROM public.novedad n
JOIN public.vehiculos v ON v.id = n.id_vehiculo
JOIN tmp_regresion_params p ON p.placa = v.placa
WHERE lower(n.tipo_novedad) = 'ingreso'
ORDER BY n.id DESC
LIMIT 1;

-- 3) Registrar salida del mismo vehículo (sin enviar id_espacio)
INSERT INTO public.novedad (tipo_novedad, id_vehiculo, fecha_hora, id_usuario, observaciones)
SELECT 'salida', v.id, now(), p.user_id, 'Salida de prueba'
FROM public.vehiculos v
JOIN tmp_regresion_params p ON p.placa = v.placa
LIMIT 1;

-- 4) Revisar última salida para esa misma placa
SELECT n.id, n.tipo_novedad, n.id_vehiculo, n.id_espacio, n.estado, n.fecha_hora
FROM public.novedad n
JOIN public.vehiculos v ON v.id = n.id_vehiculo
JOIN tmp_regresion_params p ON p.placa = v.placa
WHERE lower(n.tipo_novedad) = 'salida'
ORDER BY n.id DESC
LIMIT 1;

-- 5) Verificar que el espacio quedó libre
WITH ultima_salida AS (
	SELECT n.id
	FROM public.novedad n
	JOIN public.vehiculos v ON v.id = n.id_vehiculo
	JOIN tmp_regresion_params p ON p.placa = v.placa
	WHERE lower(n.tipo_novedad) = 'salida'
	ORDER BY n.id DESC
	LIMIT 1
)
SELECT e.id_espacio, e.numero, e.estado
FROM public.espacio e
JOIN public.novedad n ON n.id_espacio = e.id_espacio
WHERE n.id = (SELECT id FROM ultima_salida);

-- 6) Resumen final de la regresión
WITH params AS (
	SELECT * FROM tmp_regresion_params LIMIT 1
), ultimo_ingreso AS (
	SELECT n.id, n.id_espacio, n.estado
	FROM public.novedad n
	JOIN public.vehiculos v ON v.id = n.id_vehiculo
	JOIN params p ON p.placa = v.placa
	WHERE lower(n.tipo_novedad) = 'ingreso'
	ORDER BY n.id DESC
	LIMIT 1
), ultima_salida AS (
	SELECT n.id, n.id_espacio, n.estado
	FROM public.novedad n
	JOIN public.vehiculos v ON v.id = n.id_vehiculo
	JOIN params p ON p.placa = v.placa
	WHERE lower(n.tipo_novedad) = 'salida'
	ORDER BY n.id DESC
	LIMIT 1
), espacio_final AS (
	SELECT e.estado
	FROM public.espacio e
	JOIN ultima_salida s ON s.id_espacio = e.id_espacio
	LIMIT 1
)
SELECT
	(SELECT placa FROM params) AS placa_probada,
	(SELECT id FROM ultimo_ingreso) AS ingreso_id,
	(SELECT estado FROM ultimo_ingreso) AS ingreso_estado,
	(SELECT id FROM ultima_salida) AS salida_id,
	(SELECT estado FROM ultima_salida) AS salida_estado,
	(SELECT estado FROM espacio_final) AS estado_espacio_post_salida,
	CASE
		WHEN (SELECT id FROM ultimo_ingreso) IS NULL THEN 'REVISAR: no se registró ingreso'
		WHEN (SELECT id FROM ultima_salida) IS NULL THEN 'REVISAR: no se registró salida'
		WHEN (SELECT estado FROM ultima_salida) NOT IN ('finalizado', 'registrado') THEN 'REVISAR: estado de salida inesperado'
		WHEN (SELECT estado FROM espacio_final) <> 'libre' THEN 'REVISAR: espacio no quedó libre'
		ELSE 'OK'
	END AS resultado_regresion;

DROP TABLE IF EXISTS tmp_regresion_params;

-- 7) Confirmación final visible (debe aparecer como último resultado)
SELECT 'SCRIPT_EJECUTADO_COMPLETO' AS estado_script;

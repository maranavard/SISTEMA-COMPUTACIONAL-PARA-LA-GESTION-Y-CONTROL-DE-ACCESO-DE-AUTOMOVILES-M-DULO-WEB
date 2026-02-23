# Ejecución en pgAdmin (migraciones y validación)

Fecha: 2026-02-23

## 1) Base objetivo

- Conectarse a la base `sistema_control`.
- Abrir `Query Tool` sobre esa base.

## 2) Orden de ejecución recomendado

1. Ejecutar migraciones históricas pendientes:
   - `sql/migraciones/002_placa_unica.sql`
   - `sql/migraciones/004_indexes_and_seq.sql`
   - `sql/migraciones/005_modelo_lstm_ajustes.sql`
2. Ejecutar migración de modelo de negocio:
   - `sql/migraciones/006_roles_usuarios_visitantes_documentos.sql`
3. Ejecutar corrección de funciones/triggers:
   - `sql/migraciones/007_fix_novedad_triggers_and_functions.sql`

## 3) Verificación técnica

Ejecutar:

- `sql/pruebas/00_verificacion_bd_sprint1.sql`

Validaciones esperadas:

- Existe trigger `trg_novedad_asignacion` en `public.novedad`.
- Existe trigger `trg_audit_novedades` en `public.novedad`.
- No existe función legacy `fn_novedad_space_manage`.
- Las salidas nuevas deben registrar `estado = 'finalizado'` cuando se logra asociar espacio.

## 4) Prueba funcional de regresión

Ejecutar:

- `sql/pruebas/01_regresion_ingreso_salida.sql`

Ajustar previamente en el script:

- `ABC123` por una placa real existente.
- `1` por un `id_usuario` real existente.

Resultado esperado:

1. El ingreso ocupa un espacio compatible.
2. La salida recupera/libera el mismo espacio.
3. El espacio queda en estado `libre` al final.

## 5) Si falla algo

- Copiar error completo de la pestaña `Messages`.
- Compartir consulta ejecutada y mensaje exacto para diagnóstico.
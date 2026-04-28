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

## 6) Generación y exportación del MER en pgAdmin

### 6.1 Preparación

1. Abrir pgAdmin y conectarse al servidor PostgreSQL.
2. Ir a la base `sistema_control`.
3. Verificar que el esquema activo sea `public`.

### 6.2 Abrir la herramienta de ERD

1. Abrir `Tools` -> `ERD Tool`.
2. Seleccionar esquema `public`.
3. Agregar las tablas al lienzo:
   - Opción completa: todas las tablas de `public`.
   - Opción funcional: solo las tablas del flujo principal (roles, usuarios, conductores, tipo_vehiculo, vehiculos, espacio, novedad, visitantes, autorizaciones_visitante, tipo_documento, documentos_vehiculo, sync_pendientes, sync_eventos_web, predicciones, asignaciones_log).

### 6.3 Ordenar y revisar relaciones

1. Ejecutar `Auto Layout` para ordenar automáticamente.
2. Verificar visualmente relaciones clave:
   - `usuarios.idrol` -> `roles.idrol`
   - `conductores.user_id` -> `usuarios.id`
   - `vehiculos.conductor_id` -> `conductores.id`
   - `vehiculos.tipo_vehiculo_id` -> `tipo_vehiculo.id`
   - `visitantes.id_conductor` -> `conductores.id`
   - `visitantes.id_vehiculo` -> `vehiculos.id`
   - `visitantes.id_autorizado_por` -> `usuarios.id`
   - `autorizaciones_visitante.visitante_id` -> `visitantes.id`
   - `documentos_vehiculo.tipo_documento_id` -> `tipo_documento.id`

### 6.4 Exportación

1. Guardar el archivo editable del diagrama (`.pgerd`).
2. Exportar imagen para el informe (`PNG` o `SVG`).
3. Si es para impresión, usar la mayor resolución posible.

### 6.5 Evidencia mínima a incluir en el informe

1. Captura del MER completo (todas las tablas).
2. Captura del MER funcional (tablas núcleo del proceso).
3. Párrafo de validación técnica con:
   - Total de tablas en `public`: `22`.
   - Faltantes del núcleo MER: ninguno.
   - Estado final: apto para exportación y sustentación.
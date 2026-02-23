# Diseño de Base de Datos — Sprint 1

Fecha: 2026-02-23

## Objetivo

Extender el esquema actual para cubrir autenticación por roles, conductor, visitantes y documentos, reutilizando tablas existentes `vehiculos`, `novedad` y `espacio`.

## Tablas nuevas propuestas

1. `roles`
   - Catálogo de roles del sistema.
   - Campos: `id`, `codigo`, `nombre`, `activo`.

2. `usuarios`
   - Credenciales y datos base del usuario web.
   - Campos: `id`, `username`, `email`, `password_hash`, `rol_id`, `estado`, `nombres`, `apellidos`, `numero_identificacion`, `dependencia`, `created_at`, `updated_at`.

3. `conductores`
   - Perfil ampliado de conductor asociado a usuario.
   - Campos: `id`, `usuario_id`, `telefono`, `tipo_conductor`, `numero_pase`, `categoria_pase`, `fecha_registro_pase`, `fecha_vencimiento_pase`, `estado`.

4. `visitantes`
   - Registro anticipado de visitas.
   - Campos: `id`, `nombres`, `apellidos`, `numero_identificacion`, `area_destino`, `motivo_visita`, `placa`, `fecha_hora_registro`, `fecha_hora_prevista`, `estado`, `registrado_por_usuario_id`.

5. `autorizaciones_visitante`
   - Decisión de autorización/rechazo por funcionario responsable.
   - Campos: `id`, `visitante_id`, `autorizado_por_usuario_id`, `estado`, `observacion`, `fecha_decision`.

6. `tipo_documento`
   - Catálogo de documentos vehiculares.
   - Campos: `id`, `codigo`, `nombre`, `descripcion`, `entidad_objetivo`, `activo`.

7. `documentos_vehiculo`
   - Metadatos de documentos asociados a vehículo.
   - Campos: `id`, `vehiculo_id`, `tipo_documento_id`, `archivo_url`, `fecha_registro`, `fecha_vencimiento`, `estado`.

8. `sync_pendientes`
   - Cola de sincronización para continuidad offline.
   - Campos: `id`, `tabla_origen`, `registro_id`, `tipo_operacion`, `payload`, `estado`, `intentos`, `ultimo_error`, `created_at`, `updated_at`.

## Relaciones clave

- `usuarios.rol_id` -> `roles.id`
- `conductores.usuario_id` -> `usuarios.id`
- `visitantes.registrado_por_usuario_id` -> `usuarios.id`
- `autorizaciones_visitante.visitante_id` -> `visitantes.id`
- `autorizaciones_visitante.autorizado_por_usuario_id` -> `usuarios.id`
- `documentos_vehiculo.vehiculo_id` -> `vehiculos.id`
- `documentos_vehiculo.tipo_documento_id` -> `tipo_documento.id`

## Reglas de negocio de Sprint 1

- Solo `funcionario` y `admin` pueden registrar visitantes.
- Solo `seguridad` y `admin` pueden validar/controlar ingresos y espacios.
- Solo usuario activo puede autenticarse.
- Un `usuario` puede tener cero o un perfil de `conductor`.
- Un vehículo puede tener múltiples documentos y múltiples novedades.

## Compatibilidad con esquema existente

- Se conserva la lógica actual de trigger para asignar/liberar espacios en `novedad`.
- Se conserva la indexación previa sobre `vehiculos`, `espacio` y `novedad`.
- Se agrega `id_usuario` en novedades futuras vía backend para trazabilidad.

## Fuera de Sprint 1

- Predicción LSTM operativa en línea con asignación automática avanzada.
- Visualización gráfica avanzada del plano con estados en tiempo real por WebSocket.
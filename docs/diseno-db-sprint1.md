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

## Estado real validado para MER (2026-04-27)

Se validó el esquema real en PostgreSQL (`public`) y se confirmó que está listo para generar el Modelo Entidad-Relación (MER) de entrega.

### Tablas existentes en el esquema `public`

- `predicciones`
- `vehiculos`
- `usuarios`
- `asignaciones_log`
- `config_horario_universidad`
- `config_festivos_universidad`
- `config_areas_destino`
- `sync_eventos_web`
- `sync_pendientes`
- `autorizaciones_visitante`
- `roles`
- `novedad`
- `tipo_documento`
- `documentos_vehiculo`
- `novedades_audit`
- `espacio`
- `visitantes`
- `control_hardware_estado`
- `conductores`
- `tipo_vehiculo`
- `control_hardware_eventos`
- `tipo_doc`

### Descripción por tabla (formato para exposición)

| Tabla | Propósito | Relación principal |
|---|---|---|
| `predicciones` | Almacena resultados del modelo predictivo de ocupación (horizonte, paso, timestamp y versión de modelo). | Se integra con operación mediante trazabilidad en `asignaciones_log` y uso analítico del módulo de acceso. |
| `vehiculos` | Registra los vehículos asociados al sistema (placa, marca, color). | FK hacia `conductores` y `tipo_vehiculo`; referenciada por `novedad`, `visitantes` y `documentos_vehiculo`. |
| `usuarios` | Contiene credenciales y datos base de acceso web. | FK hacia `roles`; referenciada por `conductores`, `visitantes`, `autorizaciones_visitante`, `novedad` y `asignaciones_log`. |
| `asignaciones_log` | Bitácora histórica de asignaciones/liberaciones de espacios por usuario y vehículo. | Registra eventos vinculados a `usuarios`, `vehiculos` y `espacio`. |
| `config_horario_universidad` | Parametriza horarios de operación institucional (franjas y días activos). | Tabla de parametrización consumida por reglas de validación de acceso. |
| `config_festivos_universidad` | Registra fechas no laborables para ajustar reglas de acceso. | Tabla de soporte para validaciones de operación por calendario. |
| `config_areas_destino` | Catálogo de áreas de destino para visitantes. | Referencia funcional para registros en `visitantes`. |
| `sync_eventos_web` | Almacena eventos de integración/sincronización enviados desde el módulo web. | Complementa la cola de `sync_pendientes`. |
| `sync_pendientes` | Cola de operaciones pendientes de sincronización (entidad, operación, payload, intentos y errores). | Soporte transversal para sincronización entre componentes. |
| `autorizaciones_visitante` | Gestiona decisiones de autorización/rechazo para solicitudes de visitante. | FK hacia `visitantes`; referencia de usuario responsable (`usuarios`). |
| `roles` | Catálogo de perfiles de autorización del sistema. | Referenciada por `usuarios` para control de permisos. |
| `novedad` | Tabla central de eventos de acceso (ingreso/salida). | FK hacia `usuarios`, `vehiculos` y `espacio`; auditada en `novedades_audit`. |
| `tipo_documento` | Catálogo normalizado de tipos documentales exigidos para control vehicular. | Referenciada por `documentos_vehiculo`. |
| `documentos_vehiculo` | Repositorio de metadatos documentales asociados a cada vehículo. | FK hacia `vehiculos` y `tipo_documento`. |
| `novedades_audit` | Historial de auditoría de cambios en `novedad`. | Referencia `novedad` y usuario responsable de la operación. |
| `espacio` | Inventario de cupos/parqueaderos con su estado y características. | Referenciada por `novedad` y `asignaciones_log`. |
| `visitantes` | Registro de visitantes y su contexto operativo (conductor, vehículo, usuario, motivo y estado). | FK hacia `conductores`, `vehiculos` y `usuarios`; referenciada por `autorizaciones_visitante`. |
| `control_hardware_estado` | Mantiene el estado actual de dispositivos/actuadores del sistema físico. | Tabla operativa del módulo de hardware. |
| `conductores` | Perfil operativo del conductor vinculado a usuario (identificación, pase, categoría y estado). | FK hacia `usuarios`; referenciada por `vehiculos` y `visitantes`. |
| `tipo_vehiculo` | Catálogo de clasificación vehicular para reglas de acceso y asignación. | Referenciada por `vehiculos` y usada en reglas de `espacio`. |
| `control_hardware_eventos` | Bitácora de eventos recibidos desde hardware (fuente, tipo, payload, trazas y estado). | Relación funcional con `control_hardware_estado` y trazabilidad operativa. |
| `tipo_doc` | Catálogo auxiliar heredado para tipificación documental. | Se conserva por compatibilidad histórica; coexistencia con `tipo_documento`. |

### Verificación de consistencia

- Total de tablas en `public`: `22`.
- Tablas faltantes del núcleo funcional del MER: ninguna.
- Tablas extra frente al inventario esperado: ninguna.
- Relaciones (FK) clave verificadas: correctas entre `usuarios`-`roles`, `conductores`-`usuarios`, `vehiculos`-`conductores`, `visitantes`-`vehiculos`/`conductores`/`usuarios` y `autorizaciones_visitante`-`visitantes`.

### Criterio de aptitud

Con este estado, la base está en condición **APTA** para exportar y presentar el MER.

### Nota de alcance para el documento

La tabla `tipo_doc` permanece como catálogo adicional. Para el MER funcional principal del módulo web se utiliza `tipo_documento` junto con `documentos_vehiculo`.

## Descripción para el informe: MER completo y MER funcional

### 1) Descripción del MER completo

El MER completo representa la totalidad de entidades del esquema `public` de la base de datos `sistema_control`, incluyendo módulos transversales de operación, configuración, trazabilidad, sincronización y control de hardware. Este diagrama permite evidenciar la integridad global del sistema y su capacidad para soportar tanto el proceso principal de control de acceso vehicular como procesos de soporte.

En el MER completo se observan cuatro bloques de información:

- **Núcleo operativo de acceso**: `usuarios`, `roles`, `conductores`, `vehiculos`, `tipo_vehiculo`, `visitantes`, `autorizaciones_visitante`, `espacio`, `novedad`.
- **Documentación y cumplimiento**: `tipo_documento`, `documentos_vehiculo`, `novedades_audit`.
- **Sincronización y analítica**: `sync_pendientes`, `sync_eventos_web`, `predicciones`, `asignaciones_log`.
- **Configuración e integración de infraestructura**: `config_horario_universidad`, `config_festivos_universidad`, `config_areas_destino`, `control_hardware_estado`, `control_hardware_eventos`, `tipo_doc`.

Este diagrama tiene valor técnico porque permite verificar la cohesión entre módulos y la trazabilidad de los datos desde el ingreso de un vehículo hasta el registro de novedades, autorizaciones, auditoría y eventos de hardware.

### 2) Descripción del MER funcional

El MER funcional abstrae el modelo completo y conserva únicamente las entidades críticas para el flujo de negocio principal del proyecto: gestión y control de acceso de automóviles. Su finalidad es facilitar la comprensión de la lógica del sistema en escenarios de sustentación, documentación académica y validación de requisitos funcionales.

El MER funcional prioriza las siguientes entidades: `roles`, `usuarios`, `conductores`, `tipo_vehiculo`, `vehiculos`, `espacio`, `novedad`, `visitantes`, `autorizaciones_visitante`, `tipo_documento`, `documentos_vehiculo`, `sync_pendientes`, `sync_eventos_web`, `predicciones`, `asignaciones_log`.

La diferencia principal frente al MER completo es que se reduce la carga visual y se enfatiza la cadena de valor del proceso de acceso vehicular: autenticación y rol, registro/consulta de conductor y vehículo, validación de visitante, asignación/liberación de espacio, registro de novedad y soporte de trazabilidad operativa.

### 3) Explicación de relaciones clave (texto sugerido)

Las relaciones del modelo reflejan reglas de negocio del dominio institucional. Un `usuario` pertenece a un `rol`, lo que determina permisos de operación. Un `conductor` se asocia a un `usuario` y puede registrar uno o varios `vehiculos`, cada uno clasificado por `tipo_vehiculo`.

El módulo de visitantes se articula mediante la entidad `visitantes`, que referencia al conductor, al vehículo y al usuario que autoriza el ingreso. Sobre este registro se establece `autorizaciones_visitante`, donde se almacena la decisión de aprobación o rechazo.

El control de ocupación se modela con `espacio` y `novedad`: cada novedad registra eventos de ingreso/salida y se vincula con usuario, vehículo y espacio, permitiendo auditoría operativa. Adicionalmente, `documentos_vehiculo` y `tipo_documento` soportan verificación documental, mientras que `sync_pendientes`, `sync_eventos_web` y `asignaciones_log` proveen continuidad operativa y trazabilidad técnica.

### 4) Texto breve para sustentación oral

El MER completo demuestra que la base de datos no solo cubre el flujo funcional de acceso vehicular, sino también componentes de soporte como sincronización, auditoría y control de hardware. El MER funcional, por su parte, presenta de forma concentrada las entidades y relaciones críticas del proceso principal, facilitando la validación de requisitos y la lectura del modelo por parte de jurados y usuarios no técnicos. Ambos diagramas son consistentes entre sí y se derivan de un único esquema validado en PostgreSQL.
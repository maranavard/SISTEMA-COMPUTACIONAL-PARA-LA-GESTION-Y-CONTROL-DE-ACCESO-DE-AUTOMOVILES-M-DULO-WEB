# Diccionario de Datos Actualizado

Fecha: 2026-04-28

## Tablas vigentes (22)

| Nombre | Descripcion |
|---|---|
| ASIGNACIONES_LOG | Almacena el historial de asignaciones de espacio de parqueo (manuales o automaticas). |
| AUTORIZACIONES_VISITANTE | Almacena las decisiones de aprobacion/rechazo de visitantes y su trazabilidad. |
| CONDUCTORES | Almacena informacion de los conductores registrados en el sistema. |
| CONFIG_AREAS_DESTINO | Catalogo de areas de destino habilitadas para visitantes. |
| CONFIG_FESTIVOS_UNIVERSIDAD | Define fechas festivas para reglas operativas de acceso. |
| CONFIG_HORARIO_UNIVERSIDAD | Define franjas horarias y dias activos de operacion institucional. |
| CONTROL_HARDWARE_ESTADO | Almacena el estado actual de dispositivos de hardware integrados. |
| CONTROL_HARDWARE_EVENTOS | Almacena eventos recibidos desde hardware para auditoria tecnica. |
| DOCUMENTOS_VEHICULO | Almacena documentos asociados a vehiculos para validacion. |
| ESPACIO | Almacena la informacion de los espacios/cupos de parqueo y su estado. |
| NOVEDAD | Almacena eventos de ingreso, salida y novedades operativas del control vehicular. |
| NOVEDADES_AUDIT | Almacena la auditoria de cambios de estado sobre las novedades. |
| PREDICCIONES | Almacena resultados del modelo predictivo de ocupacion del parqueadero. |
| ROLES | Almacena los roles del sistema para control de permisos. |
| SYNC_EVENTOS_WEB | Almacena eventos sincronizados desde la web. |
| SYNC_PENDIENTES | Almacena eventos pendientes por sincronizar. |
| TIPO_DOC | Almacena tipos de documento heredados para compatibilidad historica. |
| TIPO_DOCUMENTO | Almacena el catalogo normalizado de tipos de documento del modulo web. |
| TIPO_VEHICULO | Almacena los tipos de vehiculo registrados en el sistema. |
| USUARIOS | Almacena la informacion de autenticacion y perfil de usuarios del sistema. |
| VEHICULOS | Almacena la informacion de los vehiculos registrados para control de acceso. |
| VISITANTES | Almacena los registros de visitantes y su trazabilidad de autorizacion. |

## TABLA 1: ASIGNACIONES_LOG
Almacena el historial de asignaciones de espacio de parqueo (manuales o automaticas).

| Columna | Tipo de dato | Tamano | Clave primaria | Clave foranea | Nulo |
|---|---|---:|:---:|---|:---:|
| id | integer | 32 | PK |  | NO |
| fecha | timestamp without time zone | - |  |  | SI |
| id_usuario | integer | 32 |  |  | SI |
| id_vehiculo | integer | 32 |  |  | SI |
| id_espacio | integer | 32 |  |  | SI |
| metodo | character varying | 20 |  |  | SI |
| motivo | text | - |  |  | SI |
| estado | character varying | 20 |  |  | SI |

## TABLA 2: AUTORIZACIONES_VISITANTE
Almacena las decisiones de aprobacion/rechazo de visitantes y su trazabilidad.

| Columna | Tipo de dato | Tamano | Clave primaria | Clave foranea | Nulo |
|---|---|---:|:---:|---|:---:|
| id | integer | 32 | PK |  | NO |
| visitante_id | integer | 32 |  | FK -> VISITANTES.id | SI |
| usuario_id | integer | 32 |  | FK -> USUARIOS.id | SI |
| estado | character varying | 20 |  |  | SI |
| observacion | text | - |  |  | SI |
| fecha | timestamp without time zone | - |  |  | SI |

## TABLA 3: CONDUCTORES
Almacena informacion de los conductores registrados en el sistema.

| Columna | Tipo de dato | Tamano | Clave primaria | Clave foranea | Nulo |
|---|---|---:|:---:|---|:---:|
| id | integer | 32 | PK |  | NO |
| user_id | integer | 32 |  | FK -> USUARIOS.id | SI |
| nombre | character varying | 100 |  |  | NO |
| apellido | character varying | 100 |  |  | SI |
| cedula | character varying | 30 |  |  | SI |
| email | character varying | 100 |  |  | SI |
| telefono | character varying | 20 |  |  | SI |
| dependencia | character varying | 100 |  |  | SI |
| tipo | character varying | 30 |  |  | SI |
| fecha_vencimiento_pase | date | - |  |  | SI |
| fecha_registro | timestamp without time zone | - |  |  | SI |
| estado | character varying | 30 |  |  | SI |
| numero_pase | character varying | 50 |  |  | SI |
| categoria pase | integer | 32 |  |  | SI |

## TABLA 4: CONFIG_AREAS_DESTINO
Catalogo de areas de destino habilitadas para visitantes.

| Columna | Tipo de dato | Tamano | Clave primaria | Clave foranea | Nulo |
|---|---|---:|:---:|---|:---:|
| id | integer | 32 | PK |  | NO |
| nombre | character varying | 80 |  |  | NO |
| activo | boolean | - |  |  | NO |
| created_at | timestamp without time zone | - |  |  | NO |
| updated_at | timestamp without time zone | - |  |  | NO |

## TABLA 5: CONFIG_FESTIVOS_UNIVERSIDAD
Define fechas festivas para reglas operativas de acceso.

| Columna | Tipo de dato | Tamano | Clave primaria | Clave foranea | Nulo |
|---|---|---:|:---:|---|:---:|
| fecha | date | - | PK |  | NO |
| descripcion | character varying | 120 |  |  | SI |
| updated_at | timestamp without time zone | - |  |  | NO |

## TABLA 6: CONFIG_HORARIO_UNIVERSIDAD
Define franjas horarias y dias activos de operacion institucional.

| Columna | Tipo de dato | Tamano | Clave primaria | Clave foranea | Nulo |
|---|---|---:|:---:|---|:---:|
| id | smallint | 16 | PK |  | NO |
| hora_inicio | time without time zone | - |  |  | NO |
| hora_fin | time without time zone | - |  |  | NO |
| dias_activos | character varying | 40 |  |  | NO |
| updated_at | timestamp without time zone | - |  |  | NO |

## TABLA 7: CONTROL_HARDWARE_ESTADO
Almacena el estado actual de dispositivos de hardware integrados.

| Columna | Tipo de dato | Tamano | Clave primaria | Clave foranea | Nulo |
|---|---|---:|:---:|---|:---:|
| clave | character varying | 80 | PK |  | NO |
| nombre | character varying | 120 |  |  | NO |
| descripcion | character varying | 240 |  |  | SI |
| encendido | boolean | - |  |  | NO |
| updated_by | integer | 32 |  |  | SI |
| updated_at | timestamp without time zone | - |  |  | NO |

## TABLA 8: CONTROL_HARDWARE_EVENTOS
Almacena eventos recibidos desde hardware para auditoria tecnica.

| Columna | Tipo de dato | Tamano | Clave primaria | Clave foranea | Nulo |
|---|---|---:|:---:|---|:---:|
| event_id | character varying | 80 | PK |  | NO |
| event_type | character varying | 60 |  |  | NO |
| source_device | character varying | 120 |  |  | NO |
| occurred_at | timestamp without time zone | - |  |  | NO |
| schema_version | character varying | 20 |  |  | NO |
| payload | jsonb | - |  |  | NO |
| trace | jsonb | - |  |  | SI |
| received_at | timestamp without time zone | - |  |  | NO |
| status | character varying | 20 |  |  | NO |

## TABLA 9: DOCUMENTOS_VEHICULO
Almacena documentos asociados a vehiculos para validacion.

| Columna | Tipo de dato | Tamano | Clave primaria | Clave foranea | Nulo |
|---|---|---:|:---:|---|:---:|
| id | integer | 32 | PK |  | NO |
| vehiculo_id | integer | 32 |  |  | NO |
| tipo_documento_id | integer | 32 |  | FK -> TIPO_DOCUMENTO.id | NO |
| archivo_url | text | - |  |  | SI |
| fecha_registro | date | - |  |  | NO |
| fecha_vencimiento | date | - |  |  | SI |
| estado | character varying | 20 |  |  | NO |
| created_at | timestamp without time zone | - |  |  | NO |
| updated_at | timestamp without time zone | - |  |  | NO |

## TABLA 10: ESPACIO
Almacena la informacion de los espacios/cupos de parqueo y su estado.

| Columna | Tipo de dato | Tamano | Clave primaria | Clave foranea | Nulo |
|---|---|---:|:---:|---|:---:|
| id_espacio | integer | 32 | PK |  | NO |
| numero | character varying | 10 |  |  | NO |
| ubicacion | character varying | 100 |  |  | SI |
| estado | character varying | 20 |  |  | SI |
| tipo_vehiculo_id | integer | 32 |  |  | SI |
| fecha_actualizacion | timestamp without time zone | - |  |  | SI |

## TABLA 11: NOVEDAD
Almacena eventos de ingreso, salida y novedades operativas del control vehicular.

| Columna | Tipo de dato | Tamano | Clave primaria | Clave foranea | Nulo |
|---|---|---:|:---:|---|:---:|
| id | integer | 32 | PK |  | NO |
| tipo_novedad | character varying | 50 |  |  | NO |
| id_vehiculo | integer | 32 |  | FK -> VEHICULOS.id | SI |
| fecha_hora | timestamp without time zone | - |  |  | SI |
| observaciones | text | - |  |  | SI |
| id_usuario | integer | 32 |  | FK -> USUARIOS.id | SI |
| id_espacio | integer | 32 |  | FK -> ESPACIO.id_espacio | SI |
| estado | text | - |  |  | SI |

## TABLA 12: NOVEDADES_AUDIT
Almacena la auditoria de cambios de estado sobre las novedades.

| Columna | Tipo de dato | Tamano | Clave primaria | Clave foranea | Nulo |
|---|---|---:|:---:|---|:---:|
| id | integer | 32 | PK |  | NO |
| nov_id | integer | 32 |  |  | SI |
| operacion | character varying | 10 |  |  | SI |
| old_estado | character varying | 50 |  |  | SI |
| new_estado | character varying | 50 |  |  | SI |
| fecha | timestamp with time zone | - |  |  | SI |
| usuario_id | integer | 32 |  |  | SI |
| observacion | text | - |  |  | SI |

## TABLA 13: PREDICCIONES
Almacena resultados del modelo predictivo de ocupacion del parqueadero.

| Columna | Tipo de dato | Tamano | Clave primaria | Clave foranea | Nulo |
|---|---|---:|:---:|---|:---:|
| id | integer | 32 | PK |  | NO |
| fecha_generacion | timestamp without time zone | - |  |  | SI |
| horizonte_minutos | integer | 32 |  |  | NO |
| paso | integer | 32 |  |  | NO |
| timestamp_prediccion | timestamp without time zone | - |  |  | NO |
| espacios_libres_pred | integer | 32 |  |  | NO |
| modelo_version | character varying | 50 |  |  | SI |

## TABLA 14: ROLES
Almacena los roles del sistema para control de permisos.

| Columna | Tipo de dato | Tamano | Clave primaria | Clave foranea | Nulo |
|---|---|---:|:---:|---|:---:|
| idrol | integer | 32 | PK |  | NO |
| name | character varying | 50 |  |  | NO |

## TABLA 15: SYNC_EVENTOS_WEB
Almacena eventos sincronizados desde la web.

| Columna | Tipo de dato | Tamano | Clave primaria | Clave foranea | Nulo |
|---|---|---:|:---:|---|:---:|
| id | bigint | 64 | PK |  | NO |
| entidad | character varying | 80 |  |  | NO |
| operacion | character varying | 40 |  |  | NO |
| payload | jsonb | - |  |  | NO |
| created_at | timestamp without time zone | - |  |  | NO |

## TABLA 16: SYNC_PENDIENTES
Almacena eventos pendientes por sincronizar.

| Columna | Tipo de dato | Tamano | Clave primaria | Clave foranea | Nulo |
|---|---|---:|:---:|---|:---:|
| id | bigint | 64 | PK |  | NO |
| entidad | character varying | 80 |  |  | NO |
| operacion | character varying | 40 |  |  | NO |
| payload | jsonb | - |  |  | NO |
| intentos | integer | 32 |  |  | NO |
| estado | character varying | 20 |  |  | NO |
| ultimo_error | text | - |  |  | SI |
| created_at | timestamp without time zone | - |  |  | NO |
| updated_at | timestamp without time zone | - |  |  | NO |

## TABLA 17: TIPO_DOC
Almacena tipos de documento heredados para compatibilidad historica.

| Columna | Tipo de dato | Tamano | Clave primaria | Clave foranea | Nulo |
|---|---|---:|:---:|---|:---:|
| id | integer | 32 | PK |  | NO |
| nombre | character varying | 50 |  |  | NO |
| descripcion | text | - |  |  | SI |

## TABLA 18: TIPO_DOCUMENTO
Almacena el catalogo normalizado de tipos de documento del modulo web.

| Columna | Tipo de dato | Tamano | Clave primaria | Clave foranea | Nulo |
|---|---|---:|:---:|---|:---:|
| id | integer | 32 | PK |  | NO |
| codigo | character varying | 30 |  |  | NO |
| nombre | character varying | 100 |  |  | NO |
| descripcion | text | - |  |  | SI |
| entidad_objetivo | character varying | 30 |  |  | NO |
| activo | boolean | - |  |  | NO |
| created_at | timestamp without time zone | - |  |  | NO |

## TABLA 19: TIPO_VEHICULO
Almacena los tipos de vehiculo registrados en el sistema.

| Columna | Tipo de dato | Tamano | Clave primaria | Clave foranea | Nulo |
|---|---|---:|:---:|---|:---:|
| id | integer | 32 | PK |  | NO |
| nombre | character varying | 50 |  |  | NO |

## TABLA 20: USUARIOS
Almacena la informacion de autenticacion y perfil de usuarios del sistema.

| Columna | Tipo de dato | Tamano | Clave primaria | Clave foranea | Nulo |
|---|---|---:|:---:|---|:---:|
| id | integer | 32 | PK |  | NO |
| username | character varying | - |  |  | NO |
| email | character varying | - |  |  | NO |
| password | character varying | - |  |  | NO |
| role | array | - |  |  | SI |
| estado | character varying | 20 |  |  | SI |
| idrol | integer | 32 |  | FK -> ROLES.idrol | SI |
| nombre | character varying | 100 |  |  | SI |
| apellido | character varying | 100 |  |  | SI |

## TABLA 21: VEHICULOS
Almacena la informacion de los vehiculos registrados para control de acceso.

| Columna | Tipo de dato | Tamano | Clave primaria | Clave foranea | Nulo |
|---|---|---:|:---:|---|:---:|
| id | integer | 32 | PK |  | NO |
| placa | character varying | - |  |  | NO |
| marca | character varying | 50 |  |  | SI |
| conductor_id | integer | 32 |  | FK -> CONDUCTORES.id | SI |
| tipo_vehiculo_id | integer | 32 |  | FK -> TIPO_VEHICULO.id | SI |
| color | character varying | 20 |  |  | SI |

## TABLA 22: VISITANTES
Almacena los registros de visitantes y su trazabilidad de autorizacion.

| Columna | Tipo de dato | Tamano | Clave primaria | Clave foranea | Nulo |
|---|---|---:|:---:|---|:---:|
| id | integer | 32 | PK |  | NO |
| id_conductor | integer | 32 |  | FK -> CONDUCTORES.id | SI |
| id_usuario_registra | integer | 32 |  | FK -> USUARIOS.id | SI |
| fecha_registro | timestamp without time zone | - |  |  | SI |
| id_vehiculo | integer | 32 |  | FK -> VEHICULOS.id | SI |
| concepto | character varying | 255 |  |  | SI |
| motivo | text | - |  |  | SI |
| id_autorizado_por | integer | 32 |  | FK -> USUARIOS.id | SI |

## Equivalencias con nombres legacy

| Nombre anterior | Nombre actual | Estado |
|---|---|---|
| CONDUCTORS | CONDUCTORES | Renombrada en el diccionario |
| DOCUMENTOS | DOCUMENTOS_VEHICULO | Reemplazada por modelo normalizado |
| REGISTRO_VISITANTES | VISITANTES | Reemplazada por tabla vigente |
| SYNC_PENDIENTES_LOCAL | SYNC_PENDIENTES | Reemplazada por tabla vigente |
| TEST_CONEXION | (sin uso actual) | No existe en el esquema vigente |

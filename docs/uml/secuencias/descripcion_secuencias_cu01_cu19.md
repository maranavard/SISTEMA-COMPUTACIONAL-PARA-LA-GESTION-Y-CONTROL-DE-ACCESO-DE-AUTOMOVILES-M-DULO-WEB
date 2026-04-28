# Descripcion de Diagramas de Secuencia (CU01-CU25)

## CU01 - Gestionar usuarios y roles
- Objetivo: Administrar altas, ediciones y cambios de estado/rol de usuarios.
- Participantes: Administrador, UI Web, UsersRoutes, UserModel, PostgreSQL.
- Flujo principal: el administrador abre modulo, envia formulario, backend valida y persiste en BD.
- Resultado: usuario creado/actualizado y confirmacion en interfaz.

## CU02 - Consultar reportes
- Objetivo: Visualizar reportes operativos del sistema.
- Participantes: Administrador o Vigilante/Seguridad, UI Web, ReportesRoutes, modelos de datos, PostgreSQL.
- Flujo principal: seleccion de tipo de reporte, validacion de alcance por rol, consulta SQL, render del resultado.
- Resultado: reporte mostrado en pantalla.

## CU03 - Exportar reportes
- Objetivo: Descargar o imprimir reportes en XLSX/PDF.
- Participantes: Administrador, UI Web, ReportesRoutes, generador de archivo, PostgreSQL.
- Flujo principal: carga de datos, construccion de archivo y entrega al navegador.
- Resultado: archivo exportado o vista imprimible.

## CU04 - Consultar historial de novedades
- Objetivo: Auditar novedades con filtros por placa/tipo/fecha.
- Participantes: Usuario autenticado, UI Web, NovedadesRoutes, NovedadModel, PostgreSQL.
- Flujo principal: envio de filtros, validacion de alcance por rol y despliegue de tabla.
- Resultado: historial filtrado visible para auditoria.

## CU05 - Consultar por placa
- Objetivo: Consultar detalle de un vehiculo por placa.
- Participantes: Usuario autenticado, UI Web, ConsultasRoutes, VehiculoModel, PostgreSQL.
- Flujo principal: ingreso de placa, consulta por modelo y retorno del detalle.
- Alterno: si no existe placa, se informa mensaje de no encontrado.

## CU06 - Iniciar sesion
- Objetivo: Autenticar usuario y abrir sesion.
- Participantes: Usuario, UI Web, AuthRoutes, UserModel, Flask-Login, PostgreSQL.
- Flujo principal: validacion de credenciales y creacion de sesion.
- Alterno: credenciales invalidas generan mensaje de error.

## CU07 - Cerrar sesion
- Objetivo: Finalizar sesion activa de forma segura.
- Participantes: Usuario, UI Web, AuthRoutes, Flask-Login.
- Flujo principal: solicitud de logout y cierre de sesion.
- Resultado: redireccion a login.

## CU08 - Validar acceso vehicular
- Objetivo: Autorizar/rechazar ingreso o salida por placa.
- Participantes: Administrador o Vigilante, UI Web, ControlAccesosRoutes, VehiculoModel, NovedadModel, PostgreSQL.
- Flujo principal: validacion documental, registro de movimiento y respuesta de acceso.
- Alternos: placa no registrada, documento vencido o bloqueo operativo.

## CU09 - Gestionar espacios de parqueo
- Objetivo: Cambiar estado de cupos y mantener disponibilidad actualizada.
- Participantes: Administrador o Vigilante, UI Web, EspaciosRoutes, EspacioModel, PostgreSQL.
- Flujo principal: consulta de estado de espacios, actualizacion operativa y confirmacion.
- Resultado: espacio actualizado en tiempo real.

## CU10 - Asignacion automatica de cupo
- Objetivo: Asignar cupo automaticamente al validar ingreso.
- Participantes: Administrador o Vigilante, UI Web, EspaciosRoutes, VehiculoModel, NovedadModel, PostgreSQL.
- Flujo principal: validacion documental, intento de asignacion automatica y respuesta de disponibilidad.
- Resultado: cupo asignado o notificacion de no disponibilidad.

## CU11 - Registrar novedad
- Objetivo: Registrar incidentes o eventos vehiculares.
- Participantes: Usuario autenticado, UI Web, NovedadesRoutes, NovedadModel, PostgreSQL.
- Flujo principal: diligenciamiento de formulario, insercion en BD y confirmacion.
- Resultado: novedad almacenada y trazable.

## CU12 - Autorizar/Rechazar visitante
- Objetivo: Cambiar estado de una solicitud de visitante.
- Participantes: Administrador o Vigilante, UI Web, ControlAccesosRoutes, VisitanteModel, PostgreSQL.
- Flujo principal: seleccion de solicitud y actualizacion de estado.
- Resultado: visitante autorizado o rechazado.

## CU13 - Registrarse en el sistema
- Objetivo: Crear cuenta nueva con rol permitido para autorregistro.
- Participantes: Publico sin sesion, UI Web, AuthRoutes, UserModel, PostgreSQL.
- Flujo principal: validacion de datos, validacion de rol permitido y alta en usuarios.
- Alterno: datos duplicados o invalidos impiden registro.

## CU14 - Gestionar perfil de conductor
- Objetivo: Actualizar datos personales y de pase.
- Participantes: Usuario autenticado, UI Web, ConductoresRoutes, ConductorModel, PostgreSQL.
- Flujo principal: consulta de perfil y validacion de permisos para gestion sensible.
- Resultado: perfil consultado o actualizado segun permisos.

## CU15 - Gestionar vehiculo propio
- Objetivo: Registrar o editar vehiculo asociado.
- Participantes: Usuario autenticado, UI Web, VehiculosRoutes, VehiculoModel, PostgreSQL.
- Flujo principal: consulta de vehiculo y validacion de permisos para gestion sensible.
- Alterno: placa duplicada genera error.

## CU16 - Recuperar contrasena
- Objetivo: Restablecer clave por correo con token seguro.
- Participantes: Usuario, UI Web, AuthRoutes, UserModel, Servicio de correo, PostgreSQL.
- Flujo principal: solicitud de enlace, validacion de token y cambio de clave.
- Alternos: correo inexistente o token expirado.

## CU17 - Registrar visitante anticipado
- Objetivo: Crear solicitud previa de visita.
- Participantes: Usuario autorizado (Administrador/Estudiante/Docente/Funcionario), UI Web, VisitantesRoutes, VisitanteModel, PostgreSQL.
- Flujo principal: registro de datos de visita, validacion de rol permitido y almacenamiento.
- Resultado: solicitud creada para autorizacion posterior.

## CU18 - Consultar estado de visitante
- Objetivo: Verificar estado de autorizacion de solicitudes.
- Participantes: Administrador o Vigilante, UI Web, ControlAccesosRoutes, VisitanteModel, PostgreSQL.
- Flujo principal: carga de solicitudes y visualizacion de estados en modulo operativo.
- Resultado: estado mostrado (pendiente/aprobado/rechazado).

## CU19 - Consultar estado de solicitud (Visitante)
- Objetivo: Permitir al visitante conocer su estado de ingreso.
- Participantes: Visitante externo, canal web publico, modulo de consulta, VisitanteModel, PostgreSQL.
- Estado actual: pendiente de implementacion.
- Flujo previsto: consulta por identificador y retorno de estado.

## CU20 - Gestionar areas destino
- Objetivo: Crear y actualizar catalogo de areas destino.
- Participantes: Administrador, UI Web, AreasRoutes, AreaDestinoModel, PostgreSQL.
- Flujo principal: registro/edicion de area y persistencia en BD.
- Resultado: catalogo de areas actualizado.

## CU21 - Configurar horarios y festivos
- Objetivo: Definir ventana operativa y calendario de festivos.
- Participantes: Administrador, UI Web, HorariosRoutes, HorarioOperacionModel, PostgreSQL.
- Flujo principal: envio de configuracion y actualizacion en BD.
- Resultado: reglas de operacion actualizadas.

## CU22 - Control manual de hardware
- Objetivo: Operar manualmente talanquera y semaforos.
- Participantes: Administrador o Vigilante, UI Web, ControlHardwareRoutes, ControlHardwareModel, PostgreSQL.
- Flujo principal: cambio de estado de dispositivos y guardado.
- Resultado: estado de hardware actualizado.

## CU23 - Recibir eventos hardware por API
- Objetivo: Ingerir eventos fisicos por API JSON con token.
- Participantes: Integracion tecnica hardware, API ControlHardware, ControlHardwareRoutes, ControlHardwareModel, PostgreSQL.
- Flujo principal: validacion de token/payload, registro de evento y respuesta de aceptacion.
- Resultado: evento aceptado, duplicado o rechazado.

## CU24 - Procesar eventos por archivos compartidos
- Objetivo: Ingerir eventos hardware desde carpeta compartida.
- Participantes: Administrador, UI Web, ControlHardwareRoutes, procesador de lote, ControlHardwareModel, PostgreSQL.
- Flujo principal: lectura de archivos, validacion, registro de eventos y clasificacion processed/error.
- Resultado: lote procesado con resumen.

## CU25 - Auditar eventos hardware
- Objetivo: Visualizar trazabilidad de eventos de hardware.
- Participantes: Administrador, UI Web, ControlHardwareRoutes, ControlHardwareModel, PostgreSQL.
- Flujo principal: consulta de eventos recientes y render en tabla de auditoria.
- Resultado: trazabilidad visible para supervision.

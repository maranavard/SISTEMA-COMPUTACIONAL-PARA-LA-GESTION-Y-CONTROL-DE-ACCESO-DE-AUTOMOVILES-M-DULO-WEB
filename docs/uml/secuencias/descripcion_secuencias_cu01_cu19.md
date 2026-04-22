
# Descripcion de Diagramas de Secuencia (CU01-CU19)

## CU01 - Gestionar usuarios y roles
- Objetivo: Administrar altas, ediciones y cambios de estado/rol de usuarios.
- Participantes: Administrador, UI Web, UsersRoutes, UserModel, PostgreSQL.
- Flujo principal: el administrador abre modulo, envia formulario, backend valida y persiste en BD.
- Resultado: usuario creado/actualizado y confirmacion en interfaz.

## CU02 - Consultar reportes
- Objetivo: Visualizar reportes operativos del sistema.
- Participantes: Administrador, UI Web, ReportesRoutes, modelos de datos, PostgreSQL.
- Flujo principal: seleccion de tipo de reporte, consulta SQL, render del resultado.
- Resultado: reporte mostrado en pantalla.

## CU03 - Exportar reportes
- Objetivo: Descargar o imprimir reportes en XLSX/PDF.
- Participantes: Administrador, UI Web, ReportesRoutes, generador de archivo, PostgreSQL.
- Flujo principal: carga de datos, construccion de archivo y entrega al navegador.
- Resultado: archivo exportado o vista imprimible.

## CU04 - Consultar historial de novedades
- Objetivo: Auditar novedades con filtros por placa/tipo/fecha.
- Participantes: Administrador, UI Web, NovedadesRoutes, NovedadModel, PostgreSQL.
- Flujo principal: envio de filtros, consulta filtrada y despliegue de tabla.
- Resultado: historial filtrado visible para auditoria.

## CU05 - Consultar por placa
- Objetivo: Consultar detalle de un vehiculo por placa.
- Participantes: Usuario, UI Web, ConsultasRoutes, VehiculoModel, PostgreSQL.
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
- Participantes: Vigilante, UI Web, ControlAccesosRoutes, VehiculoModel, NovedadModel, PostgreSQL.
- Flujo principal: validacion documental, registro de movimiento y respuesta de acceso.
- Alternos: placa no registrada, documento vencido o bloqueo operativo.

## CU09 - Gestionar espacios de parqueo
- Objetivo: Cambiar estado de cupos y mantener disponibilidad actualizada.
- Participantes: Vigilante, UI Web, EspaciosRoutes, EspacioModel, PostgreSQL.
- Flujo principal: seleccion de cupo, actualizacion de estado y confirmacion.
- Resultado: espacio actualizado en tiempo real.

## CU10 - Asignacion automatica de cupo
- Objetivo: Asignar cupo automaticamente al validar ingreso.
- Participantes: Vigilante, ControlAccesosRoutes, NovedadModel, EspacioModel, PostgreSQL.
- Flujo principal: intento de asignacion SQL; si falla, fallback manual web.
- Resultado: cupo asignado o notificacion de no disponibilidad.

## CU11 - Registrar novedad
- Objetivo: Registrar incidentes o eventos vehiculares.
- Participantes: Vigilante, UI Web, NovedadesRoutes, NovedadModel, PostgreSQL.
- Flujo principal: diligenciamiento de formulario, insercion en BD y confirmacion.
- Resultado: novedad almacenada y trazable.

## CU12 - Autorizar/Rechazar visitante
- Objetivo: Cambiar estado de una solicitud de visitante.
- Participantes: Vigilante, UI Web, ControlAccesosRoutes, VisitanteModel, PostgreSQL.
- Flujo principal: seleccion de solicitud y actualizacion de estado.
- Resultado: visitante autorizado o rechazado.

## CU13 - Registrarse en el sistema
- Objetivo: Crear cuenta nueva (perfil estudiante).
- Participantes: Estudiante, UI Web, AuthRoutes, UserModel, PostgreSQL.
- Flujo principal: validacion de datos y alta en usuarios.
- Alterno: datos duplicados o invalidos impiden registro.

## CU14 - Gestionar perfil de conductor
- Objetivo: Actualizar datos personales y de pase.
- Participantes: Estudiante, UI Web, ConductoresRoutes, ConductorModel, PostgreSQL.
- Flujo principal: envio de cambios y persistencia en tabla de conductores.
- Resultado: perfil actualizado.

## CU15 - Gestionar vehiculo propio
- Objetivo: Registrar o editar vehiculo asociado.
- Participantes: Estudiante, UI Web, VehiculosRoutes, VehiculoModel, PostgreSQL.
- Flujo principal: create/update del vehiculo con validaciones.
- Alterno: placa duplicada genera error.

## CU16 - Recuperar contrasena
- Objetivo: Restablecer clave por correo con token seguro.
- Participantes: Usuario, UI Web, AuthRoutes, UserModel, Servicio de correo, PostgreSQL.
- Flujo principal: solicitud de enlace, validacion de token y cambio de clave.
- Alternos: correo inexistente o token expirado.

## CU17 - Registrar visitante anticipado
- Objetivo: Crear solicitud previa de visita.
- Participantes: Funcionario, UI Web, VisitantesRoutes, VisitanteModel, PostgreSQL.
- Flujo principal: registro de datos de visita y almacenamiento.
- Resultado: solicitud creada para autorizacion posterior.

## CU18 - Consultar estado de visitante (Funcionario)
- Objetivo: Verificar estado de autorizacion de solicitudes.
- Participantes: Funcionario, UI Web, rutas de consulta, VisitanteModel, PostgreSQL.
- Flujo principal: busqueda por documento y lectura de estado.
- Resultado: estado mostrado (pendiente/aprobado/rechazado).

## CU19 - Consultar estado de solicitud (Visitante)
- Objetivo: Permitir al visitante conocer su estado de ingreso.
- Participantes: Visitante, UI Web, modulo de consulta, VisitanteModel, PostgreSQL.
- Flujo principal: consulta por dato identificador y retorno de estado.
- Alterno: solicitud inexistente.

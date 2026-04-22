## 2.3.8 DIAGRAMAS DE ACTIVIDADES

### Descripción general
El diagrama de actividades es un artefacto UML de comportamiento que permite representar, de forma secuencial, las tareas y decisiones que componen un proceso funcional del sistema. Este tipo de diagrama muestra con claridad el flujo de trabajo desde el inicio hasta el fin de una operación, incluyendo caminos alternos de ejecución cuando una condición no se cumple.

Su utilidad principal en este proyecto es describir cómo se ejecutan las actividades operativas del módulo web de control de acceso vehicular: validaciones, registros, autorizaciones, asignación de cupos, consultas y manejo de excepciones. En términos prácticos, estos diagramas sirven para estandarizar el proceso, facilitar pruebas funcionales, apoyar capacitación de usuarios y mantener trazabilidad entre requerimientos, lógica de negocio y operación real.

---

### CU01 - Gestionar usuarios y roles
Describe el flujo de administración de usuarios: ingreso al módulo, selección de operación (crear/editar/inactivar), diligenciamiento de datos y validación antes de guardar. Si los datos son válidos, el sistema persiste cambios; de lo contrario, informa el error.
- Diagrama: [CU01_actividad_gestion_usuarios_roles.png](docs/uml/render/actividades_cu/CU01_actividad_gestion_usuarios_roles.png)

### CU02 - Consultar reportes
Modela la consulta de reportes operativos: selección de tipo de reporte, ejecución de búsqueda y visualización. Si no hay datos disponibles, se presenta un mensaje de resultado vacío.
- Diagrama: [CU02_actividad_consultar_reportes.png](docs/uml/render/actividades_cu/CU02_actividad_consultar_reportes.png)

### CU03 - Exportar reportes
Representa el proceso de exportación de reportes en formatos XLSX/PDF, desde la selección del formato hasta la descarga o impresión. Contempla el flujo alterno en caso de error de generación.
- Diagrama: [CU03_actividad_exportar_reportes.png](docs/uml/render/actividades_cu/CU03_actividad_exportar_reportes.png)

### CU04 - Consultar historial de novedades
Muestra el proceso de filtrado del historial de novedades por placa, tipo y fecha. Incluye la visualización de resultados y el camino alterno cuando no existen coincidencias.
- Diagrama: [CU04_actividad_historial_novedades.png](docs/uml/render/actividades_cu/CU04_actividad_historial_novedades.png)

### CU05 - Consultar por placa
Describe la actividad de consulta de un vehículo por placa, con bifurcación para mostrar detalle cuando existe registro o mensaje de no encontrado cuando no existe.
- Diagrama: [CU05_actividad_consultar_placa.png](docs/uml/render/actividades_cu/CU05_actividad_consultar_placa.png)

### CU06 - Iniciar sesión
Representa autenticación de usuario: ingreso de credenciales, validación y acceso al dashboard según rol. Incluye manejo de credenciales inválidas.
- Diagrama: [CU06_actividad_iniciar_sesion.png](docs/uml/render/actividades_cu/CU06_actividad_iniciar_sesion.png)

### CU07 - Cerrar sesión
Modela el cierre de sesión desde la interfaz, finalización de sesión activa y redirección al inicio de autenticación.
- Diagrama: [CU07_actividad_cerrar_sesion.png](docs/uml/render/actividades_cu/CU07_actividad_cerrar_sesion.png)

### CU08 - Validar acceso vehicular
Describe el flujo de validación de entrada/salida por placa: captura de datos, validación documental, decisión de autorización y registro final del movimiento.
- Diagrama: [CU08_actividad_validar_acceso_vehicular.png](docs/uml/render/actividades_cu/CU08_actividad_validar_acceso_vehicular.png)

### CU09 - Gestionar espacios de parqueo
Representa el cambio de estado de cupos (disponible/ocupado/inhabilitado), validación y persistencia de actualización.
- Diagrama: [CU09_actividad_gestionar_espacios.png](docs/uml/render/actividades_cu/CU09_actividad_gestionar_espacios.png)

### CU10 - Asignación automática de cupo
Modela la asignación de cupo en función de la disponibilidad: si hay cupo, se asigna y registra; si no, se informa la no disponibilidad.
- Diagrama: [CU10_actividad_asignacion_automatica.png](docs/uml/render/actividades_cu/CU10_actividad_asignacion_automatica.png)

### CU11 - Registrar novedad
Describe la creación de una novedad operativa desde formulario, validación de campos y almacenamiento en historial.
- Diagrama: [CU11_actividad_registrar_novedad.png](docs/uml/render/actividades_cu/CU11_actividad_registrar_novedad.png)

### CU12 - Autorizar/Rechazar visitante
Representa la decisión sobre solicitudes de visitantes: selección del registro y cambio de estado a autorizado o rechazado.
- Diagrama: [CU12_actividad_autorizar_rechazar_visitante.png](docs/uml/render/actividades_cu/CU12_actividad_autorizar_rechazar_visitante.png)

### CU13 - Registrarse en el sistema
Modela el registro de estudiantes en el sistema con validación de datos y confirmación de creación de cuenta.
- Diagrama: [CU13_actividad_registrarse.png](docs/uml/render/actividades_cu/CU13_actividad_registrarse.png)

### CU14 - Gestionar perfil de conductor
Describe la actualización de información personal y documental del conductor, con validación y persistencia.
- Diagrama: [CU14_actividad_gestionar_perfil_conductor.png](docs/uml/render/actividades_cu/CU14_actividad_gestionar_perfil_conductor.png)

### CU15 - Gestionar vehículo propio
Representa el registro o edición del vehículo del usuario, incluyendo validación de placa disponible.
- Diagrama: [CU15_actividad_gestionar_vehiculo.png](docs/uml/render/actividades_cu/CU15_actividad_gestionar_vehiculo.png)

### CU16 - Recuperar contraseña
Modela el flujo de recuperación por correo: solicitud, envío de enlace, validación de token y actualización de credenciales.
- Diagrama: [CU16_actividad_recuperar_contrasena.png](docs/uml/render/actividades_cu/CU16_actividad_recuperar_contrasena.png)

### CU17 - Registrar visitante anticipado
Describe el registro previo de visita por parte del funcionario, validación del formulario y creación de la solicitud.
- Diagrama: [CU17_actividad_registrar_visitante_anticipado.png](docs/uml/render/actividades_cu/CU17_actividad_registrar_visitante_anticipado.png)

### CU18 - Consultar estado de visitante
Modela la consulta del estado de autorización de un visitante por documento, mostrando estado o no encontrado.
- Diagrama: [CU18_actividad_consultar_estado_visitante.png](docs/uml/render/actividades_cu/CU18_actividad_consultar_estado_visitante.png)

### CU19 - Consultar estado de solicitud
Representa la verificación del estado de solicitud por parte del visitante con manejo de resultado encontrado/no encontrado.
- Diagrama: [CU19_actividad_consultar_estado_solicitud.png](docs/uml/render/actividades_cu/CU19_actividad_consultar_estado_solicitud.png)

## 2.3.3 DIAGRAMAS DE SECUENCIA

### Descripción general
El diagrama de secuencia es un modelo UML de comportamiento que representa, en orden cronológico, la interacción entre actores y componentes del sistema para ejecutar un proceso específico. Este tipo de diagrama permite identificar con precisión qué elemento inicia cada acción, qué mensajes se intercambian y en qué momento se producen validaciones, decisiones o respuestas del sistema.

En términos funcionales, este diagrama sirve para: (i) verificar que el flujo implementado en el software coincide con el flujo esperado del negocio, (ii) evidenciar responsabilidades entre interfaz, lógica de negocio y base de datos, (iii) documentar escenarios alternos y manejo de errores, y (iv) facilitar el análisis técnico durante pruebas, mantenimiento y sustentación del proyecto.

En este proyecto, el diagrama de secuencia modela el flujo **login + validación de acceso vehicular**, incluyendo:
- autenticación del usuario en `auth.routes`;
- consulta de usuario y validación de contraseña en `User`;
- validación documental por placa en `Vehiculo`;
- registro de ingreso/salida en `Novedad`;
- asignación de cupo (función SQL y fallback manual con `Espacio`);
- sincronización a BD local con `LocalSyncService`.

### Diagrama
- Fuente PlantUML: [docs/uml/secuencia_login_validacion_vehicular.puml](docs/uml/secuencia_login_validacion_vehicular.puml)
- Imagen PNG: [docs/uml/render/secuencia_login_validacion_vehicular.png](docs/uml/render/secuencia_login_validacion_vehicular.png)

---

## 2.3.4 DIAGRAMAS DE ACTIVIDADES

### Descripción general
El diagrama de actividades es un modelo UML de comportamiento que describe, paso a paso, cómo se ejecuta un proceso dentro del sistema desde su inicio hasta su finalización. Este diagrama representa el flujo de tareas, las decisiones, las bifurcaciones y los posibles caminos alternos, permitiendo visualizar de forma clara la dinámica operativa del proceso analizado.

En términos funcionales, sirve para: (i) comprender la lógica del negocio de manera secuencial, (ii) identificar puntos de validación y control, (iii) documentar rutas de excepción ante fallos o condiciones no satisfactorias, y (iv) apoyar la estandarización del procedimiento para actividades de implementación, prueba y mejora continua.

Para el sistema de control de acceso vehicular, se documentó el proceso operativo de portería:
- captura de placa y tipo de movimiento;
- validación de documentación del conductor/vehículo;
- decisión de permitir o bloquear ingreso automático;
- asignación de cupo (automática o por fallback manual);
- registro de novedad de ingreso/salida;
- sincronización local y notificación al operador.

### Diagrama
- Fuente PlantUML: [docs/uml/actividades_control_acceso.puml](docs/uml/actividades_control_acceso.puml)
- Imagen PNG: [docs/uml/render/actividades_control_acceso.png](docs/uml/render/actividades_control_acceso.png)

---

## 2.3.5 DIAGRAMA DE CLASES

### Descripción general
El diagrama de clases describe la estructura estática del sistema: clases principales, atributos, métodos y dependencias entre módulos. Es clave para explicar cómo está organizado el código fuente y cómo se distribuyen las responsabilidades técnicas.

### Diagrama
- Fuente PlantUML: [docs/uml/diagrama_clases.puml](docs/uml/diagrama_clases.puml)
- Imagen PNG: [docs/uml/render/diagrama_clases.png](docs/uml/render/diagrama_clases.png)

### Descripción por clase

**1) User (modelo de autenticación y administración de usuarios)**
- Responsabilidad: representar usuarios del sistema y soportar autenticación/autorización básica.
- Funciones principales: búsqueda por id/username/email, listado, creación/edición, cambio de contraseña y verificación de credenciales.
- Ubicación en código: python/webapp/app/models/user.py.
- Pantallazo sugerido: declaración de la clase y métodos principales (get_by_id, create_user, verify_password).

**2) Vehiculo (modelo de vehículos)**
- Responsabilidad: gestionar información de vehículos y validación documental por placa.
- Funciones principales: CRUD, consulta por placa/id y estado documental.
- Ubicación en código: python/webapp/app/models/vehiculo.py.
- Pantallazo sugerido: clase Vehiculo + métodos list_items, get_by_placa, create_item.

**3) Novedad (modelo de ingresos/salidas)**
- Responsabilidad: registrar eventos operativos del parqueadero (ingreso, salida, reportes).
- Funciones principales: register_ingreso_by_placa, register_salida_by_placa, list_recent.
- Ubicación en código: python/webapp/app/models/novedad.py.
- Pantallazo sugerido: clase Novedad + métodos de ingreso/salida.

**4) Espacio (modelo de cupos/parqueaderos)**
- Responsabilidad: administrar cupos de estacionamiento y estado operativo.
- Funciones principales: consulta por número/id, upsert, construcción de slots y resumen.
- Ubicación en código: python/webapp/app/models/espacio.py.
- Pantallazo sugerido: clase Espacio + métodos list_items y upsert_by_numero.

**5) Visitante (modelo de control de visitantes)**
- Responsabilidad: registrar y actualizar visitantes.
- Funciones principales: list_items, create_item, update_item.
- Ubicación en código: python/webapp/app/models/visitante.py.
- Pantallazo sugerido: clase Visitante completa.

**6) Conductor (modelo de conductores)**
- Responsabilidad: administrar información de conductores.
- Funciones principales: list_items, create_item, update_item.
- Ubicación en código: python/webapp/app/models/conductor.py.
- Pantallazo sugerido: clase Conductor completa.

**7) DocumentoVehiculo (modelo documental)**
- Responsabilidad: gestionar documentos obligatorios del vehículo y su vigencia.
- Funciones principales: upsert_documents, get_vehicle_documents, get_status_summary.
- Ubicación en código: python/webapp/app/models/documento_vehiculo.py.
- Pantallazo sugerido: clase DocumentoVehiculo + método get_status_summary.

**8) AreaDestino (modelo de configuración de áreas)**
- Responsabilidad: administrar catálogo de áreas destino para visitantes.
- Funciones principales: list_items, create_area, update_area, delete_area.
- Ubicación en código: python/webapp/app/models/area_destino.py.
- Pantallazo sugerido: clase AreaDestino + métodos create_area y update_area.

**9) HorarioOperacion (modelo de configuración horaria y festivos)**
- Responsabilidad: definir horario operativo y días festivos del sistema.
- Funciones principales: get_config, update_config, evaluate_moment.
- Ubicación en código: python/webapp/app/models/horario.py.
- Pantallazo sugerido: clase HorarioOperacion + método evaluate_moment.

**10) ControlHardware (modelo de control y auditoría hardware)**
- Responsabilidad: administrar estados manuales de dispositivos y eventos técnicos.
- Funciones principales: list_states, update_states, register_event, list_recent_events.
- Ubicación en código: python/webapp/app/models/control_hardware.py.
- Pantallazo sugerido: clase ControlHardware + métodos register_event y list_recent_events.

**11) LocalSyncService (servicio RF18 de sincronización local)**
- Responsabilidad: sincronizar eventos web a BD local y manejar reintentos.
- Funciones principales: sync_event, retry_pending, enqueue_pending.
- Ubicación en código: python/webapp/app/utils/local_sync.py.
- Pantallazo sugerido: clase LocalSyncService + método sync_event.

**12) DB (infraestructura de conexión)**
- Responsabilidad: centralizar creación de conexiones a BD principal/local.
- Funciones principales: get_connection y get_local_connection.
- Ubicación en código: python/webapp/app/db.py.
- Pantallazo sugerido: funciones get_connection y get_local_connection.

**13) AuthZ (autorización por rol)**
- Responsabilidad: normalizar rol y restringir acceso por decoradores.
- Funciones principales: normalize_role, roles_required, admin_required, community_required, parking_ops_required.
- Ubicación en código: python/webapp/app/utils/authz.py.
- Pantallazo sugerido: bloque de decoradores de autorización completo.

**14) AuthRoutes (blueprint de autenticación)**
- Responsabilidad: login, registro y recuperación de contraseña.
- Ubicación en código: python/webapp/app/auth/routes.py.
- Pantallazo sugerido: declaración de auth_bp y endpoint login.

**15) MainRoutes (blueprint principal)**
- Responsabilidad: navegación principal del sistema (inicio y dashboard).
- Ubicación en código: python/webapp/app/main/routes.py.
- Pantallazo sugerido: declaración de main_bp y endpoint dashboard.

**16) UsersRoutes (blueprint de usuarios)**
- Responsabilidad: gestión administrativa de usuarios.
- Ubicación en código: python/webapp/app/users/routes.py.
- Pantallazo sugerido: declaración de users_bp y endpoint index/listado.

**17) ConductoresRoutes (blueprint de conductores)**
- Responsabilidad: CRUD de conductores para operación de parqueadero.
- Ubicación en código: python/webapp/app/conductores/routes.py.
- Pantallazo sugerido: declaración de conductores_bp y endpoint crear.

**18) VehiculosRoutes (blueprint de vehículos)**
- Responsabilidad: CRUD de vehículos y validaciones asociadas.
- Ubicación en código: python/webapp/app/vehiculos/routes.py.
- Pantallazo sugerido: declaración de vehiculos_bp y endpoint guardar/crear.

**19) VisitantesRoutes (blueprint de visitantes)**
- Responsabilidad: gestión de solicitudes/registro de visitantes.
- Ubicación en código: python/webapp/app/visitantes/routes.py.
- Pantallazo sugerido: declaración de visitantes_bp y endpoint crear.

**20) EspaciosRoutes (blueprint de espacios)**
- Responsabilidad: gestión de cupos y estado de parqueaderos.
- Ubicación en código: python/webapp/app/espacios/routes.py.
- Pantallazo sugerido: declaración de espacios_bp y endpoint index.

**21) NovedadesRoutes (blueprint de novedades)**
- Responsabilidad: consulta operativa de novedades.
- Ubicación en código: python/webapp/app/novedades/routes.py.
- Pantallazo sugerido: declaración de novedades_bp y endpoint index.

**22) ReportesRoutes (blueprint de reportes)**
- Responsabilidad: visualización, impresión y exportación de reportes.
- Ubicación en código: python/webapp/app/reportes/routes.py.
- Pantallazo sugerido: declaración de reportes_bp y endpoint descargar_excel.

**23) ConsultasRoutes (blueprint de consultas)**
- Responsabilidad: consulta y gestión de registros por placa/id.
- Ubicación en código: python/webapp/app/consultas/routes.py.
- Pantallazo sugerido: declaración de consultas_bp y endpoint index.

**24) ControlAccesosRoutes (blueprint de control de acceso)**
- Responsabilidad: flujo operativo de autorización/rechazo en ingreso/salida.
- Ubicación en código: python/webapp/app/control_accesos/routes.py.
- Pantallazo sugerido: declaración de control_accesos_bp y endpoints autorizar/rechazar.

**25) HorariosRoutes (blueprint de configuración horaria)**
- Responsabilidad: configurar horario operativo y festivos.
- Ubicación en código: python/webapp/app/horarios/routes.py.
- Pantallazo sugerido: declaración de horarios_bp y endpoint guardar.

**26) AreasRoutes (blueprint de áreas destino)**
- Responsabilidad: administrar áreas destino de visitantes.
- Ubicación en código: python/webapp/app/areas/routes.py.
- Pantallazo sugerido: declaración de areas_bp y endpoint crear/actualizar.

**27) ControlHardwareRoutes (blueprint de hardware)**
- Responsabilidad: control manual de dispositivos, API de comandos e ingestión/procesamiento de eventos.
- Ubicación en código: python/webapp/app/control_hardware/routes.py.
- Pantallazo sugerido: declaración de control_hardware_bp y endpoint api_evento o procesar_archivos.

---

## 2.3.6 DIAGRAMA DE DESPLIEGUE

### Descripción general
El diagrama de despliegue representa la arquitectura física/lógica de ejecución del sistema: nodos, artefactos desplegados y canales de comunicación entre ellos. Su propósito es evidenciar dónde corre cada componente, cómo se conectan y qué dependencias externas existen.

En este proyecto se identifica una arquitectura web cliente-servidor con sincronización híbrida:
- cliente web (navegador) para operación de usuarios;
- servidor Flask como capa de aplicación;
- PostgreSQL principal como almacenamiento central;
- PostgreSQL local como contingencia/sincronización (RF18);
- servicio SMTP externo para recuperación de contraseña.

### Diagrama
- Fuente PlantUML: [docs/uml/despliegue_sistema.puml](docs/uml/despliegue_sistema.puml)
- Imagen PNG: [docs/uml/render/despliegue_sistema.png](docs/uml/render/despliegue_sistema.png)

### Nota técnica para sustentación
Se recomienda complementar este apartado con información de entorno real de ejecución (por ejemplo: sistema operativo del servidor, versión de Python, versión de PostgreSQL, red/puertos y mecanismo de respaldo), para fortalecer la trazabilidad de despliegue en la defensa del proyecto.

---

## Checklist de revisión (qué debe tener cada diagrama)

### A. Diagrama de Secuencia (2.3.3)
- [ ] Una **descripción general inicial** que explique qué es y para qué sirve.
- [ ] Identificación de **actores/líneas de vida** (usuario, UI, backend, BD, servicios).
- [ ] Flujo principal en **orden temporal** (mensajes de inicio a fin).
- [ ] Inclusión de **alternativas** (`alt/else`) para casos de error o decisiones.
- [ ] Evidencia de interacción con **persistencia** (consultas/registro en BD).
- [ ] Referencia a archivo fuente `.puml` y evidencia gráfica `.png`.

### B. Diagrama de Actividades (2.3.4)
- [ ] Una **descripción general inicial** que explique qué es y para qué sirve.
- [ ] Presencia de **inicio** y **fin** del proceso.
- [ ] Actividades redactadas con verbos de acción (capturar, validar, registrar, notificar).
- [ ] **Decisiones** claramente modeladas (condiciones Sí/No).
- [ ] Rutas alternas de excepción (por ejemplo, documentación inválida o sin cupo).
- [ ] Referencia a archivo fuente `.puml` y evidencia gráfica `.png`.

### C. Diagrama de Clases (2.3.5)
- [ ] Una **descripción general** del propósito del diagrama.
- [ ] Clases principales del sistema con **atributos/métodos representativos**.
- [ ] Dependencias/relaciones entre clases (modelo, servicio, rutas, infraestructura).
- [ ] **Descripción por cada clase**: responsabilidad, funciones principales y relación.
- [ ] Coherencia del diagrama con el código real del proyecto.
- [ ] Referencia a archivo fuente `.puml` y evidencia gráfica `.png`.

### D. Diagrama de Despliegue (2.3.6)
- [ ] Una **descripción general** de qué representa y para qué se usa.
- [ ] Nodos de ejecución identificados (cliente, servidor aplicación, BD principal, BD local).
- [ ] Canales de comunicación entre nodos (HTTP/HTTPS, SQL, sincronización, SMTP).
- [ ] Artefactos o componentes desplegados por nodo (UI, módulos Flask, servicios).
- [ ] Justificación de la arquitectura según el tipo de proyecto.
- [ ] Referencia a archivo fuente `.puml` y evidencia gráfica `.png`.

### Recomendación final para revisión con Director
- [ ] Agregar al menos un párrafo por diagrama explicando **por qué ese diagrama es relevante** para tu solución.
- [ ] Incluir numeración y títulos exactamente como exige la guía institucional (2.3.3 a 2.3.6).
- [ ] Verificar legibilidad de imágenes (tamaño de fuente y resolución) antes de exportar a Word/PDF.

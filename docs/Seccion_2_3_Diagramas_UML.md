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
- Funciones principales: búsqueda por id/username/email, listado de usuarios, creación/edición, actualización de contraseña y verificación de credenciales.
- Relación: se conecta a PostgreSQL mediante `db.get_connection()`.

**2) Vehiculo (modelo de vehículos)**
- Responsabilidad: gestionar información de vehículos y validación documental por placa.
- Funciones principales: CRUD de vehículos, consulta por placa/id, verificación de vigencia documental (estado de conductor y pase).
- Relación: usa `LocalSyncService` para sincronización de eventos y consulta BD principal.

**3) Novedad (modelo de ingresos/salidas)**
- Responsabilidad: registrar eventos operativos del parqueadero (ingreso/salida y reportes).
- Funciones principales: registrar ingreso por placa, registrar salida por placa, listar novedades recientes, crear registros para reportes.
- Relación: depende de `Espacio` para fallback de asignación y de `LocalSyncService` para sincronización.

**4) Espacio (modelo de cupos/parqueaderos)**
- Responsabilidad: administrar cupos de estacionamiento y su estado operativo.
- Funciones principales: consulta/listado de espacios, creación/edición/eliminación, búsqueda por número, construcción de malla de slots, resumen de ocupación.
- Relación: soporta la lógica de asignación usada por `Novedad`.

**5) Visitante (modelo de control de visitantes)**
- Responsabilidad: registrar y actualizar solicitudes/ingresos de visitantes.
- Funciones principales: listado y operaciones de creación/actualización.
- Relación: utilizado por rutas de `control_accesos` para autorización/rechazo.

**6) Conductor (modelo de conductores)**
- Responsabilidad: administrar datos de conductores vinculados al sistema.
- Funciones principales: listado, creación y actualización de conductores.
- Relación: su estado y vigencia documental impactan validaciones en `Vehiculo`.

**7) LocalSyncService (servicio de sincronización RF18)**
- Responsabilidad: replicar eventos web hacia base local y gestionar cola de pendientes.
- Funciones principales: `sync_event`, `retry_pending`, `enqueue_pending`, sincronización por entidad (`vehiculos`, `novedad`).
- Relación: usa `get_connection()` y `get_local_connection()` para BD principal y local.

**8) DB (infraestructura de conexión)**
- Responsabilidad: centralizar parámetros y creación de conexiones a PostgreSQL.
- Funciones principales: conexión a base principal y base local con fallback de codificación.
- Relación: clase/utilidad base consumida por modelos y servicios.

**9) AuthZ (autorización por rol)**
- Responsabilidad: normalizar rol y aplicar restricciones por permisos.
- Funciones principales: `normalize_role`, `roles_required`, `admin_required`, `community_required`.
- Relación: utilizado por blueprints/rutas protegidas.

**10) AuthRoutes, ControlAccesosRoutes, ReportesRoutes, ConsultasRoutes, MainRoutes (controladores/blueprints)**
- Responsabilidad: exponer endpoints HTTP y coordinar interacción entre UI, modelos y reglas de negocio.
- Funciones principales:
  - `AuthRoutes`: login, registro, recuperación/restablecimiento de contraseña.
  - `ControlAccesosRoutes`: validación vehicular, registro de movimientos y autorización de visitantes.
  - `ReportesRoutes`: visualización e importación/exportación de reportes (incluye Excel).
  - `ConsultasRoutes`: consulta y gestión de vehículos por placa.
  - `MainRoutes`: navegación principal (inicio, dashboard, mi cuenta).

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

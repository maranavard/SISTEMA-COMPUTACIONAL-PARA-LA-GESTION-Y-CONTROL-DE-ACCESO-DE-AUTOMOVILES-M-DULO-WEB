## 2.3.2 DIAGRAMAS DE CASOS DE USO

### Descripción general
Un diagrama de casos de uso describe las funcionalidades que el sistema ofrece a cada actor y el límite funcional del sistema. Su propósito es mostrar **qué hace** el sistema desde la perspectiva del usuario, sin entrar en detalles de implementación técnica.

En este proyecto, el diagrama de casos de uso organiza los procesos por actor: **Administrador, Vigilante/Seguridad, Estudiante, Funcionario y Visitante**.

### Diagrama
- Fuente PlantUML: [docs/uml/casos_de_uso.puml](docs/uml/casos_de_uso.puml)
- Imagen PNG: [docs/uml/render/casos_de_uso.png](docs/uml/render/casos_de_uso.png)

---

## Descripción por cada caso de uso

### ADMINISTRADOR

#### CU01. Gestionar usuarios y roles
- **Actor:** Administrador.
- **Objetivo:** Crear, editar, activar/inactivar usuarios y asignar roles.
- **Precondición:** Sesión iniciada como administrador.
- **Flujo básico:**
  1. Accede al módulo Usuarios.
  2. Selecciona crear/editar/eliminar usuario.
  3. Diligencia formulario.
  4. Guarda cambios.
- **Flujos alternos:**
  - Usuario ya existe → el sistema muestra error.
  - Datos incompletos → el sistema no permite guardar.
  - Error en base de datos → se cancela la operación.
- **Postcondición:** Usuario actualizado en base de datos.

#### CU02. Consultar reportes
- **Actor:** Administrador.
- **Objetivo:** Revisar reportes operativos del sistema.
- **Precondición:** Sesión iniciada como administrador.
- **Flujo básico:**
  1. Entra a Reportes.
  2. Selecciona tipo de reporte.
  3. Visualiza resultados.
- **Flujos alternos:**
  - No hay datos → muestra mensaje.
  - Error en consulta → muestra error.
- **Postcondición:** Información consultada y disponible para exportación.

#### CU03. Exportar reportes (XLSX/PDF)
- **Actor:** Administrador.
- **Objetivo:** Descargar o imprimir reportes.
- **Precondición:** Reporte generado en pantalla.
- **Flujo básico:**
  1. Selecciona opción Exportar.
  2. Elige formato (Excel o PDF).
  3. Descarga archivo o imprime.
- **Flujos alternos:**
  - Error en exportación → muestra mensaje.
- **Postcondición:** Archivo generado o listo para impresión.

#### CU04. Consultar historial de novedades
- **Actor:** Administrador.
- **Objetivo:** Auditar novedades por placa, tipo o fecha.
- **Precondición:** Sesión iniciada como administrador.
- **Flujo básico:**
  1. Ingresa al módulo Historial de Novedades.
  2. Aplica filtros (placa/tipo/fecha).
  3. Visualiza resultados filtrados.
- **Flujos alternos:**
  - Sin coincidencias → muestra mensaje de lista vacía.
  - Error en consulta → muestra error.
- **Postcondición:** Historial filtrado mostrado.

#### CU05. Consulta por placa
- **Actor:** Administrador.
- **Objetivo:** Consultar información de un vehículo.
- **Precondición:** Sesión iniciada.
- **Flujo básico:**
  1. Ingresa placa.
  2. Sistema consulta.
  3. Muestra resultados.
- **Flujos alternos:**
  - Placa no registrada → muestra mensaje.
- **Postcondición:** Resultado de la consulta mostrado.

#### CU06. Cerrar sesión
- **Actor:** Administrador.
- **Objetivo:** Finalizar sesión activa.
- **Precondición:** Sesión iniciada.
- **Flujo básico:**
  1. Selecciona “Cerrar sesión”.
  2. Sistema finaliza sesión.
- **Flujos alternos:**
  - Error de sesión → muestra mensaje y solicita reintento.
- **Postcondición:** Sesión cerrada correctamente.

---

### VIGILANTE / SEGURIDAD

#### CU07. Validar acceso vehicular (entrada/salida)
- **Actor:** Vigilante.
- **Objetivo:** Autorizar o rechazar acceso vehicular.
- **Precondición:** Sesión iniciada; placa ingresada.
- **Flujo básico:**
  1. Ingresa o captura la placa.
  2. Selecciona tipo (entrada/salida).
  3. Sistema valida y responde.
- **Flujos alternos:**
  - Placa no registrada → acceso denegado.
  - Usuario no autorizado/documentación inválida → rechazo.
  - Falla del sistema → registro manual.
- **Postcondición:** Ingreso/salida registrada en novedades.

#### CU08. Gestionar espacios de parqueo
- **Actor:** Vigilante.
- **Objetivo:** Administrar disponibilidad de espacios.
- **Precondición:** Sesión iniciada como vigilante.
- **Flujo básico:**
  1. Accede a Espacios.
  2. Selecciona cupo.
  3. Cambia estado.
  4. Guarda.
- **Flujos alternos:**
  - Error al guardar → mensaje.
- **Postcondición:** Estado del espacio actualizado.

#### CU09. Asignación automática de cupo por placa
- **Actor:** Vigilante.
- **Objetivo:** Asignar cupo automáticamente a vehículo válido.
- **Precondición:** Placa registrada y cupos disponibles.
- **Flujo básico:**
  1. Ingresa placa.
  2. Sistema valida.
  3. Asigna cupo.
- **Flujos alternos:**
  - Sin cupos → rechaza acceso.
  - Vehículo no registrado → error.
- **Postcondición:** Cupo asignado y novedad de ingreso registrada.

#### CU10. Registrar novedad
- **Actor:** Vigilante.
- **Objetivo:** Registrar incidentes o eventos de vehículos.
- **Precondición:** Sesión iniciada como vigilante; placa válida.
- **Flujo básico:**
  1. Abre formulario.
  2. Diligencia datos.
  3. Guarda.
- **Flujos alternos:**
  - Datos incompletos → no guarda.
- **Postcondición:** Novedad almacenada en historial.

#### CU11. Consultar por placa
- **Actor:** Vigilante.
- **Objetivo:** Ver información detallada de una placa registrada.
- **Precondición:** Sesión iniciada como vigilante.
- **Flujo básico:**
  1. Accede a Consultas.
  2. Digita placa.
  3. Visualiza resultado.
- **Flujos alternos:**
  - No existe → mensaje.
- **Postcondición:** Datos del vehículo mostrados.

#### CU12. Autorizar/Rechazar visitante
- **Actor:** Vigilante.
- **Objetivo:** Decidir ingreso de visitante registrado.
- **Precondición:** Solicitud de visitante existente.
- **Flujo básico:**
  1. Abre Autorizaciones.
  2. Selecciona solicitud.
  3. Autoriza o rechaza.
- **Flujos alternos:**
  - Fuera de horario → rechazo.
  - Solicitud inexistente → error.
- **Postcondición:** Estado de solicitud actualizado.

---

### ESTUDIANTE

#### CU13. Registrarse en el sistema
- **Actor:** Estudiante.
- **Objetivo:** Crear cuenta propia para acceso al sistema.
- **Precondición:** No tener sesión activa; datos mínimos válidos.
- **Flujo básico:**
  1. Clic en Registrarme.
  2. Diligencia el formulario.
  3. Sistema valida datos.
  4. Confirma.
- **Flujos alternos:**
  - Correo ya registrado → error.
  - Datos inválidos → no permite registro.
- **Postcondición:** Cuenta creada con rol de estudiante.

#### CU14. Iniciar sesión / Cerrar sesión
- **Actor:** Estudiante.
- **Objetivo:** Acceder o salir del sistema de forma segura.
- **Precondición:** Credenciales válidas (inicio).
- **Flujo básico:**
  1. Ingresa usuario y contraseña.
  2. Sistema valida datos.
  3. Accede al panel.
  4. Usa botón Cerrar sesión.
- **Flujos alternos:**
  - Credenciales incorrectas → error.
  - Usuario inactivo → acceso denegado.
- **Postcondición:** Sesión abierta o cerrada correctamente.

#### CU15. Gestionar perfil de conductor
- **Actor:** Estudiante.
- **Objetivo:** Registrar/actualizar datos personales y de pase.
- **Precondición:** Sesión iniciada como estudiante.
- **Flujo básico:**
  1. Abre pestaña Conductores.
  2. Edita campos.
  3. Guarda cambios.
- **Flujos alternos:**
  - Datos inválidos → no guarda.
- **Postcondición:** Perfil actualizado.

#### CU16. Gestionar vehículo propio
- **Actor:** Estudiante.
- **Objetivo:** Registrar o actualizar vehículo asociado.
- **Precondición:** Sesión iniciada; datos de vehículo disponibles.
- **Flujo básico:**
  1. Abre pestaña Vehículos.
  2. Edita o crea el registro.
  3. Guarda cambios.
- **Flujos alternos:**
  - Placa duplicada → error.
- **Postcondición:** Vehículo almacenado/actualizado.

#### CU17. Recuperar contraseña
- **Actor:** Estudiante.
- **Objetivo:** Restablecer acceso cuando olvida contraseña.
- **Precondición:** Correo registrado en el sistema.
- **Flujo básico:**
  1. Solicita recuperación.
  2. Recibe enlace por correo electrónico registrado.
  3. Cambia contraseña.
- **Flujos alternos:**
  - Correo no registrado → error.
  - Enlace expirado → solicitar nuevamente.
- **Postcondición:** Contraseña actualizada.

---

### FUNCIONARIO

#### CU18. Registrar visitante anticipado
- **Actor:** Funcionario.
- **Objetivo:** Registrar visitas previas con área destino y horario.
- **Precondición:** Sesión iniciada como funcionario.
- **Flujo básico:**
  1. Abre Visitantes.
  2. Diligencia formulario.
  3. Guarda.
- **Flujos alternos:**
  - Datos incompletos → error.
- **Postcondición:** Solicitud de visitante creada.

#### CU19. Consultar estado de autorización de visitante
- **Actor:** Funcionario.
- **Objetivo:** Ver si la visita fue autorizada o rechazada.
- **Precondición:** Existencia de solicitud registrada.
- **Flujo básico:**
  1. Busca visitante por documento.
  2. Revisa resultado.
- **Flujos alternos:**
  - No existe → mensaje.
- **Postcondición:** Estado consultado.

---

### VISITANTE

#### CU20. Consultar estado de su solicitud
- **Actor:** Visitante.
- **Objetivo:** Confirmar si puede ingresar al campus.
- **Precondición:** Solicitud registrada previamente por funcionario.
- **Flujo básico:**
  1. Proporciona documento de identidad/datos.
  2. Sistema consulta.
  3. Muestra estado.
- **Flujos alternos:**
  - No existe → no autorizado.
  - Pendiente → en espera.
- **Postcondición:** Estado informado al visitante.

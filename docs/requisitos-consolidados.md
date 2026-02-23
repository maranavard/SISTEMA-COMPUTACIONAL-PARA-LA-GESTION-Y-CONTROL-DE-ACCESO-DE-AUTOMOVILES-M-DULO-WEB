# Requisitos consolidados del proyecto

Fecha de consolidación: 2026-02-23

## 1) Roles de usuario definidos

- Administrador del sistema (`admin_sistema`): gestión total de usuarios, roles, reportes y auditoría.
- Personal de seguridad (`seguridad_udec`): validación de accesos, registro de novedades y gestión de espacios.
- Conductores (`conductor_udec`): registro de datos personales/vehiculares y consulta de estado/historial.
- Funcionario administrativo (`funcionario_area`): registro anticipado y autorización/rechazo de visitantes.

## 2) Requerimientos funcionales (RF)

- **RF01** Registro y edición de usuarios.
- **RF02** Registro y consulta de placas.
- **RF03** Gestión manual de espacios (disponible/ocupado/inhabilitado).
- **RF04** Predicción de ocupación mediante modelo LSTM.
- **RF05** Asignación automática inteligente de espacios (LSTM + estado real).
- **RF06** Validación manual de documentos (licencia, vencimientos, alertas).
- **RF07** Consulta de historial de accesos.
- **RF08** Recuperación de cuentas por correo.
- **RF09** Generación y exportación de reportes (PDF/Excel).
- **RF10** Validación automática de accesos vehiculares.
- **RF11** Consulta detallada de placas registradas.
- **RF12** Revisión de reportes de ingresos por fecha/hora.
- **RF13** Registro anticipado de visitantes por área.
- **RF14** Validación/autorización de ingreso de visitantes.
- **RF15** Registro de novedades de vehículos.
- **RF16** Visualización de novedades registradas.
- **RF17** Historial de novedades por placa/fecha.
- **RF18** Sincronización entre base web y base local.

## 3) Requerimientos no funcionales (RNF)

Nota: en el documento original vienen numerados como RF19-RF25; se normalizan aquí como RNF01-RNF07.

- **RNF01** Gestión de datos distribuida (base central + respaldo local).
- **RNF02** Interfaz accesible, clara, responsiva e intuitiva.
- **RNF03** Fiabilidad e integridad de datos con validaciones y respaldo.
- **RNF04** Arquitectura modular para mantenimiento y escalabilidad.
- **RNF05** Escalabilidad para otras sedes de la universidad.
- **RNF06** Portabilidad web (navegador moderno, sin instalación local).
- **RNF07** Eficiencia en consultas, validaciones y registros.

## 4) Requisitos de rendimiento

- Tiempo de respuesta de operaciones: < 3 segundos.
- Consultas con filtros: < 2 segundos.
- Generación/exportación de reportes: < 5 segundos.
- Carga inicial de módulos: < 2 segundos.
- Soporte de usuarios concurrentes: al menos 50.
- Disponibilidad objetivo: 99%.

## 5) Restricciones de diseño y UX

- Diseño responsivo para distintos dispositivos.
- Interfaz intuitiva para usuarios no técnicos.
- Vistas diferenciadas por perfil de usuario.
- Componentes reutilizables para tablas y formularios.
- Mensajes claros de validación/confirmación.
- Compatibilidad con navegadores modernos sin plugins.
- El plano de parqueadero lo administra solo seguridad.

## 6) Parámetros de identidad institucional (UDEC)

- Tipografía objetivo: Century Gothic.
- Alternativas de compatibilidad: Montserrat, Times New Roman.
- Colores principales:
  - Amarillo UDEC: `#FBE122`
  - Dorado: `#DAAA00`
  - Verde claro: `#007B3E`
  - Verde oscuro: `#00482B`
- Colores secundarios opcionales:
  - Naranja: `#F7931E`
  - Verde lima: `#79C000`
  - Verde medio: `#91C256`
  - Cian: `#00A99D`
  - Gris institucional: `#4D4D4D`

## 7) Alcance de datos (resumen)

- **BD principal**: usuarios, roles, conductores, vehículos, espacios, ingresos/salidas, visitantes, documentos, novedades, auditoría, reportes.
- **BD secundaria/local**: mínimo vehículos y novedades para continuidad operativa sin internet, con sincronización posterior.
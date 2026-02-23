# Backlog MVP y fases

Fecha: 2026-02-23

## Criterio de priorización

Primero se implementa lo que permite operar el acceso vehicular diario. Luego se agregan capacidades avanzadas (predicción, analítica y endurecimiento).

## Fase 1 — MVP operativo (prioridad alta)

1. Autenticación y control de acceso por roles (RF01 + permisos base).
2. Registro/edición de usuarios y estados (RF01).
3. Registro/consulta de conductores, placas y vehículos (RF02, RF11).
4. Gestión manual de espacios por seguridad (RF03).
5. Ingreso/salida vehicular con validación de placa (RF10).
6. Asignación de espacio manual y automática básica por disponibilidad actual (RF05 versión inicial, sin LSTM aún).
7. Historial de accesos y novedades (RF07, RF15, RF16, RF17).
8. Registro anticipado y validación de visitantes (RF13, RF14).
9. Reporte básico de ingresos y exportación inicial (RF09, RF12).

## Fase 2 — Inteligencia y sincronización

1. ETL de datos históricos para entrenamiento.
2. Módulo LSTM para predicción de ocupación (RF04).
3. Integración LSTM + disponibilidad real para asignación inteligente (RF05 completo).
4. Sincronización web/local robusta con reintentos y trazabilidad (RF18).
5. Alertas de documentos y vencimientos (RF06 completo).

## Fase 3 — Consolidación institucional

1. Dashboard de métricas avanzado.
2. Auditoría completa y consulta de logs por filtros.
3. Reportes por módulo con vista previa.
4. Optimización de rendimiento para metas de <3s y carga <2s.

## Entregables por sprint sugeridos

- **Sprint 1:** autenticación, usuarios/roles, conductores/vehículos.
- **Sprint 2:** espacios, ingresos/salidas, visitantes.
- **Sprint 3:** reportes, novedades, auditoría inicial.
- **Sprint 4:** LSTM + sincronización + optimización.

## Criterio de “hecho” mínimo por módulo

- CRUD funcional.
- Validaciones de negocio.
- Control de permisos por rol.
- Registro de auditoría de acciones críticas.
- Prueba funcional manual documentada.
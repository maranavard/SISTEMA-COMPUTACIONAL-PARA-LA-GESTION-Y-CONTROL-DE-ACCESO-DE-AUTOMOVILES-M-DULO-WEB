# Sistema Computacional para la Gestión y Control de Acceso de Automóviles (Módulo Web)

Este repositorio contiene la base técnica del proyecto de control de acceso vehicular para campus universitario.

## Documentación de trabajo

- [Requisitos consolidados](docs/requisitos-consolidados.md)
- [Backlog MVP y fases](docs/backlog-mvp.md)
- [Guía de trabajo segura (Git + VS Code)](docs/guia-trabajo-seguro.md)
- [Suposiciones y dependencias](docs/suposiciones-dependencias.md)
- [Diseño DB Sprint 1](docs/diseno-db-sprint1.md)
- [Ejecución en pgAdmin](docs/ejecucion-pgadmin.md)

## Estructura actual

- `sql/`: funciones, triggers, migraciones y pruebas de base de datos.
- `python/`: scripts ETL y entrenamiento de modelo LSTM.

## Siguiente objetivo

Implementar el **MVP funcional**: autenticación, gestión de usuarios/roles, registro de conductores/vehículos, control de ingresos-salidas, espacios de parqueo y reportes básicos.

## Migración nueva

- [006_roles_usuarios_visitantes_documentos.sql](sql/migraciones/006_roles_usuarios_visitantes_documentos.sql)
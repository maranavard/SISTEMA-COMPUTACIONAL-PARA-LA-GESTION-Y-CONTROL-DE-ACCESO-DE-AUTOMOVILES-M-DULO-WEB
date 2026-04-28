# Sistema Computacional para la Gestión y Control de Acceso de Automóviles (Módulo Web)

Este repositorio contiene la base técnica del proyecto de control de acceso vehicular para campus universitario.

## Documentación de trabajo

- [Requisitos consolidados](docs/requisitos-consolidados.md)
- [Backlog MVP y fases](docs/backlog-mvp.md)
- [Guía de trabajo segura (Git + VS Code)](docs/guia-trabajo-seguro.md)
- [Suposiciones y dependencias](docs/suposiciones-dependencias.md)
- [Diseño DB Sprint 1](docs/diseno-db-sprint1.md)
- [Ejecución en pgAdmin](docs/ejecucion-pgadmin.md)
- [Backend Flask Sprint 1](docs/backend-flask-sprint1.md)
- [Mapa del código Sprint 1](docs/mapa-codigo-sprint1.md)

## Estructura actual

- `sql/`: funciones, triggers, migraciones y pruebas de base de datos.
- `python/`: scripts ETL y entrenamiento de modelo LSTM.
- `python/webapp/`: backend Flask base (auth + dashboard + conexión PostgreSQL).

## Siguiente objetivo

Implementar el **MVP funcional**: autenticación, gestión de usuarios/roles, registro de conductores/vehículos, control de ingresos-salidas, espacios de parqueo y reportes básicos.

## Migración nueva

- [006_roles_usuarios_visitantes_documentos.sql](sql/migraciones/006_roles_usuarios_visitantes_documentos.sql)

## Integración hardware (API JSON)

Endpoint de recepción de eventos desde módulos físicos:

- `POST /control-hardware/api/evento`
- Header requerido: `X-Hardware-Token: <token>`
- Content-Type: `application/json`

Campos mínimos del contrato v1.0:

- `event_id` (UUID)
- `event_type` (`acceso_detectado`, `validacion_externa`, `estado_dispositivo`, `heartbeat`)
- `source_device`
- `occurred_at` (ISO-8601)
- `schema_version`
- `payload` (objeto JSON)

### Casos de prueba sugeridos

1) Evento válido (`202 Accepted`)

```bash
curl -X POST "http://127.0.0.1:5000/control-hardware/api/evento" \
	-H "Content-Type: application/json" \
	-H "X-Hardware-Token: dev-hardware-token" \
	-d '{
		"event_id": "11111111-1111-4111-8111-111111111111",
		"event_type": "acceso_detectado",
		"source_device": "cabina_norte_rpi_01",
		"occurred_at": "2026-04-26T10:45:00-05:00",
		"schema_version": "1.0",
		"payload": {
			"placa": "abc123",
			"movimiento": "entrada"
		}
	}'
```

2) Token inválido (`401 Unauthorized`)

```bash
curl -X POST "http://127.0.0.1:5000/control-hardware/api/evento" \
	-H "Content-Type: application/json" \
	-H "X-Hardware-Token: token-invalido" \
	-d '{"event_id":"22222222-2222-4222-8222-222222222222","event_type":"heartbeat","source_device":"cabina_norte_rpi_01","occurred_at":"2026-04-26T10:46:00-05:00","schema_version":"1.0","payload":{"status":"ok"}}'
```

3) Evento duplicado (`409 Conflict`)

- Reenviar exactamente el mismo `event_id` del caso 1.

4) Error de validación (`422 Unprocessable Entity`)

```bash
curl -X POST "http://127.0.0.1:5000/control-hardware/api/evento" \
	-H "Content-Type: application/json" \
	-H "X-Hardware-Token: dev-hardware-token" \
	-d '{
		"event_id": "33333333-3333-4333-8333-333333333333",
		"event_type": "acceso_detectado",
		"source_device": "cabina_norte_rpi_01",
		"occurred_at": "2026-04-26T10:47:00-05:00",
		"schema_version": "1.0",
		"payload": {
			"placa": "XYZ987",
			"movimiento": "subir"
		}
	}'
```

## Integración hardware por archivos compartidos

Para cumplir el escenario de cabina local y archivos compartidos, el módulo de control de hardware procesa lotes JSON desde carpeta compartida.

Variables de entorno:

- `HARDWARE_SHARED_INBOX` (entrada)
- `HARDWARE_SHARED_PROCESSED` (procesados)
- `HARDWARE_SHARED_ERROR` (errores)
- `HARDWARE_SHARED_MAX_BATCH` (máximo de archivos por ejecución manual)

Flujo operativo:

1. Un módulo físico deja archivos `*.json` en `HARDWARE_SHARED_INBOX`.
2. En la vista de Control de Hardware, un usuario autorizado ejecuta **Procesar archivos compartidos**.
3. Cada JSON se valida con el mismo contrato v1.0 del endpoint `POST /control-hardware/api/evento`.
4. Si el evento es válido, se registra y el archivo pasa a `processed`.
5. Si está duplicado (`event_id` ya registrado), se mueve a `processed` con prefijo `dup_`.
6. Si hay error de formato/validación, se mueve a `error` con prefijo `json_error_` o `event_error_`.
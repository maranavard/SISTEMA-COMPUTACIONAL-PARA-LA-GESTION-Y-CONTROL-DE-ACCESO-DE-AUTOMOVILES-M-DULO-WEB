# Suposiciones y dependencias del proyecto

Fecha: 2026-02-23

## Suposiciones del proyecto

1. Los usuarios tienen acceso a internet y dispositivos compatibles.
2. Cada usuario posee credenciales únicas y roles definidos.
3. Las placas y los espacios de parqueo están registrados y son únicos.
4. Las áreas responsables validan visitantes oportunamente.
5. El personal de seguridad accede al sistema de forma continua.
6. Las acciones de usuarios quedan registradas para auditoría.
7. El sistema opera en entorno autenticado y seguro.

## Flujo funcional acordado

1. Se registra un usuario con rol (`administrador`, `seguridad`, `funcionario`, `propietario`).
2. Según rol, se habilita registro como conductor (completa datos de pase/licencia).
3. Conductor registrado puede registrar vehículos.
4. Funcionario por dependencia registra visitantes (conductor/visitante/placa si aplica).
5. Área responsable autoriza o rechaza el ingreso del visitante.
6. En ingreso vehicular se identifica tipo de vehículo y se busca espacio libre compatible.
7. Se registra novedad y se actualiza espacio a `ocupado`; en salida se libera a `libre`.

## Dependencias técnicas

- Backend: Python + Flask + Flask-Login.
- Frontend: HTML + CSS + Tailwind + Jinja2.
- BD principal: PostgreSQL (`sistema_control`).
- BD secundaria local (offline): réplica mínima de `vehiculos` y `novedad` para continuidad.

## Dependencias de datos

- Catálogo de roles activo y consistente.
- Tipo de vehículo por placa para asignación de espacios.
- Catálogo de tipos de documento para vincular documentos a vehículos.
- Catálogo de espacios con tipo (`automovil`/`moto`) y estado (`libre`/`ocupado`/`inhabilitado`).

## Riesgos operativos y mitigación

- Falta de internet: operar con BD local y sincronizar pendientes al restablecer conexión.
- Datos incompletos de conductor/placa: marcar novedad como `pendiente`.
- Sin cupo disponible: registrar ingreso pendiente y reintentar asignación.

## Nota sobre el archivo de respaldo actual

El archivo [sql/sistema_control_backup.sql](../sql/sistema_control_backup.sql) parece estar en formato binario de dump (`pg_dump -Fc`), no como script plano. Para restaurarlo se usa `pg_restore`, no ejecución directa como SQL de texto.
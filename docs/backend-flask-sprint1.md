# Backend Flask Sprint 1

## Estructura creada

- `python/webapp/run.py`
- `python/webapp/requirements.txt`
- `python/webapp/.env.example`
- `python/webapp/app/` (factory, config, db, auth, main, templates, estáticos)

## Funcionalidad inicial

- Inicio de sesión con `Flask-Login`.
- Sesión persistente y cierre de sesión.
- Ruta protegida `/dashboard`.
- Módulo CRUD de usuarios en `/usuarios`.
- Módulo CRUD de conductores en `/conductores`.
- Control de autorización: solo rol admin puede gestionar usuarios.
- Conexión PostgreSQL para leer usuarios.
- Soporte de contraseña hash (`pbkdf2` / `scrypt`) y fallback a texto plano.

## Arranque local

1. Ir a carpeta:
   - `cd python/webapp`
2. Crear/activar entorno virtual.
3. Instalar dependencias:
   - `pip install -r requirements.txt`
4. Crear archivo `.env` (copiando `.env.example`) y ajustar credenciales.
5. Ejecutar:
   - `python run.py`

## Uso del módulo usuarios

- Ingresar con un usuario de rol `admin_sistema` (o `admin`/`administrador`).
- Abrir `/usuarios`.
- Desde ahí puedes:
   - Crear usuarios.
   - Editar rol/estado.
   - Cambiar contraseña.

- Desde `/conductores` puedes:
   - Crear conductores.
   - Editar datos de conductor.

## Nota de compatibilidad con BD actual

La autenticación consulta `public.usuarios` y toma rol desde:

- `usuarios.role` (si existe)
- o `roles.codigo` vía `usuarios.rol_id`

Esto permite funcionar mientras se termina de normalizar el esquema.

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

## Nota de compatibilidad con BD actual

La autenticación consulta `public.usuarios` y toma rol desde:

- `usuarios.role` (si existe)
- o `roles.codigo` vía `usuarios.rol_id`

Esto permite funcionar mientras se termina de normalizar el esquema.

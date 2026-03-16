# Mapa del código Sprint 1 (qué hace cada parte)

## Flujo general

1. El navegador abre `/auth/login`.
2. `auth/routes.py` procesa usuario/clave.
3. `models/user.py` consulta PostgreSQL y valida contraseña.
4. Si credenciales son válidas, Flask-Login crea sesión.
5. El usuario entra a `/dashboard` (ruta protegida).

## Archivos clave

- `python/webapp/run.py`
  - Arranca el servidor Flask local.
  - Modifica este archivo solo si quieres cambiar host/puerto/debug.

- `python/webapp/app/__init__.py`
  - Crea la aplicación (`create_app`).
  - Registra blueprints (`auth`, `main`).
  - Configura Flask-Login y `user_loader`.

- `python/webapp/app/config.py`
  - Lee variables de entorno (`.env`).
  - Aquí cambias configuración de DB o `SECRET_KEY`.

- `python/webapp/app/db.py`
  - Conexión a PostgreSQL.
  - Si cambias driver o pool de conexiones, empieza aquí.

- `python/webapp/app/models/user.py`
  - Modelo de usuario para login.
  - Consultas SQL para buscar usuario por `id` o `username`.
  - Verificación de contraseña (hash o texto plano).

- `python/webapp/app/auth/routes.py`
  - Rutas de autenticación: login y logout.
  - Aquí agregas recuperación de contraseña, bloqueo por intentos, etc.

- `python/webapp/app/main/routes.py`
  - Ruta raíz y dashboard protegido.
  - Aquí cuelgas módulos nuevos (usuarios, conductores, vehículos, etc.).

- `python/webapp/app/users/routes.py`
  - CRUD administrativo de usuarios.
  - Endpoints: listado, creación y actualización.

- `python/webapp/app/conductores/routes.py`
  - CRUD de conductores.
  - Endpoints: listado, creación y actualización.

- `python/webapp/app/models/conductor.py`
  - Capa SQL de conductores.
  - Compatible con tablas `conductores` o `conductors`.

- `python/webapp/app/utils/authz.py`
  - Decorador `admin_required` para restringir rutas por rol.

- `python/webapp/app/templates/login.html`
  - Vista login (HTML/Jinja2).
  - Cambios visuales o campos del formulario.

- `python/webapp/app/static/css/app.css`
  - Estilos globales y del login.
  - Ajustes visuales de colores, tamaños y espaciados.

## Qué modificar según necesidad

- **Cambiar diseño del login:**
  - `templates/login.html` + `static/css/app.css`

- **Cambiar validación de credenciales:**
  - `models/user.py` (`get_by_username`, `verify_password`)

- **Agregar rol obligatorio para admin:**
  - `utils/authz.py` (`admin_required`) y su uso en rutas.

- **Cambiar comportamiento del CRUD de usuarios:**
  - `users/routes.py` + `models/user.py` + `templates/users/index.html`

- **Cambiar comportamiento del CRUD de conductores:**
  - `conductores/routes.py` + `models/conductor.py` + `templates/conductores/index.html`

- **Cambiar conexión a base de datos:**
  - `config.py` y `db.py`

- **Agregar nuevas páginas protegidas:**
  - `main/routes.py` + nuevas plantillas en `templates/`

## Siguiente bloque recomendado

1. CRUD de vehículos.
2. Módulo de control de accesos (ingreso/salida) conectado a funciones SQL.
3. Recuperación de contraseña y política de bloqueo por intentos.
4. Reportes básicos por módulo.

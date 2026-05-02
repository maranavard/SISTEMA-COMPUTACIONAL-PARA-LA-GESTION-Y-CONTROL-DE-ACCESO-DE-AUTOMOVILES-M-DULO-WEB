"""Factory principal de Flask.

Responsabilidades:
1) Cargar configuración general.
2) Inicializar Flask-Login.
3) Registrar blueprints (módulos de rutas).
"""

import hmac
import secrets

from flask import Flask, request, session
from flask_login import LoginManager

from .config import Config
from .models.user import User
from .utils.authz import normalize_role

login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Inicia sesion para continuar."
DOCENTE_LABEL = "Docente UDEC"
CSRF_TOKEN_KEY = "_csrf_token"
CSRF_EXEMPT_ENDPOINT_PREFIXES = ("control_hardware.api_",)


@login_manager.user_loader
def load_user(user_id: str):
    # Flask-Login usa este callback para reconstruir el usuario de la sesión.
    return User.get_by_id(int(user_id))


def _is_csrf_exempt_endpoint(endpoint: str | None) -> bool:
    if not endpoint:
        return False
    return endpoint.startswith(CSRF_EXEMPT_ENDPOINT_PREFIXES)


def _get_or_create_csrf_token() -> str:
    token = session.get(CSRF_TOKEN_KEY)
    if not token:
        token = secrets.token_urlsafe(32)
        session[CSRF_TOKEN_KEY] = token
    return str(token)


def create_app() -> Flask:
    # Instancia principal de Flask.
    app = Flask(__name__)

    # Carga variables definidas en Config (DB, SECRET_KEY, etc.).
    app.config.from_object(Config)

    # Inicializa manejo de sesiones/autenticación.
    login_manager.init_app(app)

    @app.context_processor
    def inject_csrf_token():
        return {"csrf_token": _get_or_create_csrf_token}

    @app.before_request
    def enforce_csrf_protection():
        if request.method in {"GET", "HEAD", "OPTIONS", "TRACE"}:
            return None

        if _is_csrf_exempt_endpoint(request.endpoint):
            return None

        session_token = str(session.get(CSRF_TOKEN_KEY) or "")
        request_token = (
            request.form.get(CSRF_TOKEN_KEY)
            or request.headers.get("X-CSRF-Token")
            or ""
        ).strip()

        if not session_token or not request_token or not hmac.compare_digest(session_token, request_token):
            return "CSRF token inválido o ausente.", 400

        return None

    @app.template_filter("role_label")
    def role_label(value):
        role = normalize_role(value)
        if not role:
            return ""

        labels = {
            "admin_sistema": "Administrador del sistema",
            "admin": "Administrador",
            "administrador": "Administrador",
            "seguridad_udec": "Seguridad UDEC",
            "vigilante": "Vigilante / Seguridad",
            "vigilancia": "Vigilante / Seguridad",
            "funcionario_area": "Funcionario de área",
            "funcionario": "Funcionario de área",
            "conductor_udec": "Conductor UDEC",
            "estudiante_udec": "Estudiante UDEC",
            "profesor_udec": DOCENTE_LABEL,
            "docente_udec": DOCENTE_LABEL,
            "maestro_udec": DOCENTE_LABEL,
            "visitante_udec": "Visitante UDEC",
        }

        if role in labels:
            return labels[role]

        return role.replace("_", " ").strip().title()

    # Import local para evitar ciclos de importación.
    from .auth.routes import auth_bp
    from .main.routes import main_bp
    from .users.routes import users_bp
    from .conductores.routes import conductores_bp
    from .vehiculos.routes import vehiculos_bp
    from .visitantes.routes import visitantes_bp
    from .espacios.routes import espacios_bp
    from .novedades.routes import novedades_bp
    from .reportes.routes import reportes_bp
    from .consultas.routes import consultas_bp
    from .control_accesos.routes import control_accesos_bp
    from .horarios.routes import horarios_bp
    from .areas.routes import areas_bp
    from .control_hardware.routes import control_hardware_bp

    # Registro de módulos de rutas.
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(conductores_bp)
    app.register_blueprint(vehiculos_bp)
    app.register_blueprint(visitantes_bp)
    app.register_blueprint(espacios_bp)
    app.register_blueprint(novedades_bp)
    app.register_blueprint(reportes_bp)
    app.register_blueprint(consultas_bp)
    app.register_blueprint(control_accesos_bp)
    app.register_blueprint(horarios_bp)
    app.register_blueprint(areas_bp)
    app.register_blueprint(control_hardware_bp)

    return app

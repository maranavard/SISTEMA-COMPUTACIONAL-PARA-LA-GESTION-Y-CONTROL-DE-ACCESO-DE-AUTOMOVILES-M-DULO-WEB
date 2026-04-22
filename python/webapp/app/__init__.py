"""Factory principal de Flask.

Responsabilidades:
1) Cargar configuración general.
2) Inicializar Flask-Login.
3) Registrar blueprints (módulos de rutas).
"""

from flask import Flask
from flask_login import LoginManager

from .config import Config
from .models.user import User

login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Inicia sesion para continuar."


@login_manager.user_loader
def load_user(user_id: str):
    # Flask-Login usa este callback para reconstruir el usuario de la sesión.
    return User.get_by_id(int(user_id))


def create_app() -> Flask:
    # Instancia principal de Flask.
    app = Flask(__name__)

    # Carga variables definidas en Config (DB, SECRET_KEY, etc.).
    app.config.from_object(Config)

    # Inicializa manejo de sesiones/autenticación.
    login_manager.init_app(app)

    @app.template_filter("role_label")
    def role_label(value):
        role = (str(value or "").strip().lower())
        if not role:
            return ""

        labels = {
            "admin_sistema": "Administrador del sistema",
            "admin": "Administrador",
            "administrador": "Administrador",
            "seguridad_udec": "Seguridad UDEC",
            "funcionario_area": "Funcionario de área",
            "conductor_udec": "Conductor UDEC",
            "estudiante_udec": "Estudiante UDEC",
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

    return app

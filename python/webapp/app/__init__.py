from flask import Flask
from flask_login import LoginManager

from .config import Config
from .models.user import User

login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Inicia sesión para continuar."


@login_manager.user_loader
def load_user(user_id: str):
    return User.get_by_id(int(user_id))


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)

    login_manager.init_app(app)

    from .auth.routes import auth_bp
    from .main.routes import main_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

    return app

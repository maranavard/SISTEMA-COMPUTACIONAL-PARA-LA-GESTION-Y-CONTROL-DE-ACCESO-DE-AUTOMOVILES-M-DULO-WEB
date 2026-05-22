"""Configuración central de la aplicación.
 
Todos los valores sensibles o dependientes de entorno se leen desde .env.

Usa SOLO Neon PostgreSQL.

"""
 
import os

from dotenv import load_dotenv
 
load_dotenv()
 
 
class Config:

    # Clave para sesión, mensajes flash y protección de cookies.

    SECRET_KEY = os.getenv("SECRET_KEY") or "dev-local-key"
 
    # ==================================================

    # NEON POSTGRESQL (ÚNICA BASE DE DATOS)

    # ==================================================

    DATABASE_URL = os.getenv("DATABASE_URL")

    if not DATABASE_URL:

        raise ValueError("❌ DATABASE_URL no configurada. Debes configurarla en Render o .env")

    # Configuración de SQLAlchemy para Neon

    SQLALCHEMY_DATABASE_URI = DATABASE_URL

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SQLALCHEMY_ENGINE_OPTIONS = {

        'pool_size': 10,

        'pool_recycle': 300,

        'pool_pre_ping': True,

        'connect_args': {

            'sslmode': 'require',  # Neon requiere SSL

            'connect_timeout': 10

        }

    }
 
    # Configuración de correo para recuperación de contraseña (RF08).

    MAIL_HOST = os.getenv("MAIL_HOST", "")

    MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))

    MAIL_USER = os.getenv("MAIL_USER", "")

    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD") or ""

    MAIL_FROM = os.getenv("MAIL_FROM", MAIL_USER)

    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "1") in {"1", "true", "True"}

    MAIL_SUPPRESS_SEND = os.getenv("MAIL_SUPPRESS_SEND", "0") in {"1", "true", "True"}
 
    # Token de recuperación de contraseña.

    PASSWORD_RESET_SALT = os.getenv("PASSWORD_RESET_SALT") or f"{SECRET_KEY}-reset-salt"

    PASSWORD_RESET_MAX_AGE_SECONDS = int(os.getenv("PASSWORD_RESET_MAX_AGE_SECONDS", "3600"))
 
    # Token para integración JSON con módulo de hardware local.

    HARDWARE_CONTROL_TOKEN = os.getenv("HARDWARE_CONTROL_TOKEN") or ""
 
    # Canal de archivos compartidos para eventos hardware (IEEE 3.1.3/3.1.4).

    HARDWARE_SHARED_INBOX = os.getenv("HARDWARE_SHARED_INBOX", "hardware_shared/inbox")

    HARDWARE_SHARED_PROCESSED = os.getenv("HARDWARE_SHARED_PROCESSED", "hardware_shared/processed")

    HARDWARE_SHARED_ERROR = os.getenv("HARDWARE_SHARED_ERROR", "hardware_shared/error")

    HARDWARE_SHARED_MAX_BATCH = int(os.getenv("HARDWARE_SHARED_MAX_BATCH", "30"))
 

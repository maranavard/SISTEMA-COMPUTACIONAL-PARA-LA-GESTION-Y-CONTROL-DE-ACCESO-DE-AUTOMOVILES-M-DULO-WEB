"""Configuración central de la aplicación.

Todos los valores sensibles o dependientes de entorno se leen desde .env.
"""

import os
from dotenv import load_dotenv


load_dotenv()


class Config:
    # Clave para sesión, mensajes flash y protección de cookies.
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")

    # Parámetros de conexión PostgreSQL.
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", "5432"))
    DB_NAME = os.getenv("DB_NAME", "sistema_control")
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

    # BD secundaria/local para continuidad operativa y respaldo (RF18).
    LOCAL_DB_ENABLED = os.getenv("LOCAL_DB_ENABLED", "1") in {"1", "true", "True"}
    LOCAL_DB_HOST = os.getenv("LOCAL_DB_HOST", DB_HOST)
    LOCAL_DB_PORT = int(os.getenv("LOCAL_DB_PORT", str(DB_PORT)))
    LOCAL_DB_NAME = os.getenv("LOCAL_DB_NAME", "sistema_control_local")
    LOCAL_DB_USER = os.getenv("LOCAL_DB_USER", DB_USER)
    LOCAL_DB_PASSWORD = os.getenv("LOCAL_DB_PASSWORD", DB_PASSWORD)

    SYNC_MAX_RETRIES = int(os.getenv("SYNC_MAX_RETRIES", "10"))

    # Configuración de correo para recuperación de contraseña (RF08).
    MAIL_HOST = os.getenv("MAIL_HOST", "")
    MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
    MAIL_USER = os.getenv("MAIL_USER", "")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
    MAIL_FROM = os.getenv("MAIL_FROM", MAIL_USER)
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "1") in {"1", "true", "True"}
    MAIL_SUPPRESS_SEND = os.getenv("MAIL_SUPPRESS_SEND", "0") in {"1", "true", "True"}

    # Token de recuperación de contraseña.
    PASSWORD_RESET_SALT = os.getenv("PASSWORD_RESET_SALT", "password-reset-salt")
    PASSWORD_RESET_MAX_AGE_SECONDS = int(os.getenv("PASSWORD_RESET_MAX_AGE_SECONDS", "3600"))

    # Token para integración JSON con módulo de hardware local.
    HARDWARE_CONTROL_TOKEN = os.getenv("HARDWARE_CONTROL_TOKEN", "dev-hardware-token")

    # Canal de archivos compartidos para eventos hardware (IEEE 3.1.3/3.1.4).
    HARDWARE_SHARED_INBOX = os.getenv("HARDWARE_SHARED_INBOX", "hardware_shared/inbox")
    HARDWARE_SHARED_PROCESSED = os.getenv("HARDWARE_SHARED_PROCESSED", "hardware_shared/processed")
    HARDWARE_SHARED_ERROR = os.getenv("HARDWARE_SHARED_ERROR", "hardware_shared/error")
    HARDWARE_SHARED_MAX_BATCH = int(os.getenv("HARDWARE_SHARED_MAX_BATCH", "30"))

"""Helpers de acceso a base de datos.

Aquí centralizamos la forma de abrir conexión PostgreSQL para no repetir
credenciales ni lógica de conexión en cada módulo.
"""

import psycopg2
from flask import current_app


def get_connection():
    # Lee credenciales desde la configuración cargada en Flask app context.
    params = dict(
        host=current_app.config["DB_HOST"],
        port=current_app.config["DB_PORT"],
        dbname=current_app.config["DB_NAME"],
        user=current_app.config["DB_USER"],
        password=current_app.config["DB_PASSWORD"],
    )

    # Primer intento: conexión estándar.
    try:
        return psycopg2.connect(**params)
    except UnicodeDecodeError:
        # Fallback para servidores/errores en codificación LATIN1.
        try:
            conn = psycopg2.connect(**params, options="-c client_encoding=LATIN1")
            conn.set_client_encoding("LATIN1")
            return conn
        except Exception as exc:
            raise RuntimeError(
                "No fue posible conectar a PostgreSQL. Revisa DB_HOST/DB_PORT/DB_NAME/DB_USER/DB_PASSWORD en .env"
            ) from exc
    except Exception as exc:
        raise RuntimeError(
            "No fue posible conectar a PostgreSQL. Revisa DB_HOST/DB_PORT/DB_NAME/DB_USER/DB_PASSWORD en .env"
        ) from exc


def get_local_connection():
    if not current_app.config.get("LOCAL_DB_ENABLED", False):
        raise RuntimeError("Sincronización local deshabilitada (LOCAL_DB_ENABLED=0).")

    params = dict(
        host=current_app.config["LOCAL_DB_HOST"],
        port=current_app.config["LOCAL_DB_PORT"],
        dbname=current_app.config["LOCAL_DB_NAME"],
        user=current_app.config["LOCAL_DB_USER"],
        password=current_app.config["LOCAL_DB_PASSWORD"],
    )

    try:
        return psycopg2.connect(**params)
    except UnicodeDecodeError:
        try:
            conn = psycopg2.connect(**params, options="-c client_encoding=LATIN1")
            conn.set_client_encoding("LATIN1")
            return conn
        except Exception as exc:
            raise RuntimeError(
                "No fue posible conectar a PostgreSQL local. Revisa LOCAL_DB_HOST/LOCAL_DB_PORT/LOCAL_DB_NAME/LOCAL_DB_USER/LOCAL_DB_PASSWORD en .env"
            ) from exc
    except Exception as exc:
        raise RuntimeError(
            "No fue posible conectar a PostgreSQL local. Revisa LOCAL_DB_HOST/LOCAL_DB_PORT/LOCAL_DB_NAME/LOCAL_DB_USER/LOCAL_DB_PASSWORD en .env"
        ) from exc

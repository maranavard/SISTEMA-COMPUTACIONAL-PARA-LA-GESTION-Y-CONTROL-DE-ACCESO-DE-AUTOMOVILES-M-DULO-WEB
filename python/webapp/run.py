"""Punto de entrada del servidor Flask.

Este archivo solo arranca la aplicación creada en app/__init__.py.
Si en el futuro quieres usar gunicorn/uwsgi en despliegue, normalmente
apuntará al objeto `app` definido aquí.
"""

from app import create_app

# Crea la app con factory pattern.
app = create_app()

if __name__ == "__main__":
    # Modo debug para desarrollo local.
    app.run(debug=True)

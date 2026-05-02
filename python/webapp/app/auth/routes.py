"""Rutas de autenticación.

Incluye login (GET/POST) y cierre de sesión.
"""

LOGIN_ROUTE = "auth.login"
DASHBOARD_ROUTE = "main.dashboard"
REGISTER_ROUTE = "auth.register"
FORGOT_PASSWORD_ROUTE = "auth.forgot_password"
RESET_PASSWORD_ROUTE = "auth.reset_password"

import smtplib
from email.message import EmailMessage

from itsdangerous import BadSignature, URLSafeTimedSerializer
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask import current_app
from flask_login import current_user, login_user, logout_user

from app.models.user import User
from app.utils.authz import normalize_role
from app.utils.field_validators import is_valid_cedula, is_valid_email, normalize_cedula, normalize_email


auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


def _role_label(role_value: str) -> str:
    role = normalize_role(role_value)
    labels = {
        "admin_sistema": "Administrador del sistema",
        "admin": "Administrador",
        "administrador": "Administrador",
        "seguridad_udec": "Seguridad UDEC",
        "vigilante": "Vigilante / Seguridad",
        "vigilancia": "Vigilante / Seguridad",
        "funcionario_area": "Funcionario de area",
        "docente_udec": "Docente UDEC",
        "conductor_udec": "Conductor UDEC",
        "estudiante_udec": "Estudiante UDEC",
        "visitante_udec": "Visitante UDEC",
    }
    return labels.get(role, role.replace("_", " ").strip().title() if role else "Sin rol")


def _serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"])


def _generate_reset_token(email: str) -> str:
    return _serializer().dumps(email, salt=current_app.config["PASSWORD_RESET_SALT"])


def _verify_reset_token(token: str) -> str | None:
    try:
        return _serializer().loads(
            token,
            salt=current_app.config["PASSWORD_RESET_SALT"],
            max_age=current_app.config["PASSWORD_RESET_MAX_AGE_SECONDS"],
        )
    except BadSignature:
        return None


def _send_password_reset_email(to_email: str, reset_link: str) -> bool:
    if bool(current_app.config.get("MAIL_SUPPRESS_SEND")):
        print(f"[RF08-TEST] Enlace recuperación para {to_email}: {reset_link}")
        return False

    host = (current_app.config.get("MAIL_HOST") or "").strip()
    user = (current_app.config.get("MAIL_USER") or "").strip()
    password = current_app.config.get("MAIL_PASSWORD") or ""
    port = int(current_app.config.get("MAIL_PORT") or 587)
    use_tls = bool(current_app.config.get("MAIL_USE_TLS"))
    sender = (current_app.config.get("MAIL_FROM") or user).strip()

    if not host or not user or not password or not sender:
        print(
            "[RF08-TEST] SMTP incompleto. "
            f"Enlace recuperación para {to_email}: {reset_link}"
        )
        return False

    msg = EmailMessage()
    msg["Subject"] = "Restablecimiento de contraseña - Sistema Control Vehicular UDEC"
    msg["From"] = sender
    msg["To"] = to_email
    msg.set_content(
        "Se solicitó restablecer tu contraseña.\n"
        f"Ingresa al siguiente enlace: {reset_link}\n\n"
        "Si no solicitaste este cambio, ignora este correo."
    )

    with smtplib.SMTP(host, port, timeout=20) as server:
        if use_tls:
            server.starttls()
        server.login(user, password)
        server.send_message(msg)
    return True


def _validate_register_input(username: str, email: str, password: str, confirm_password: str, numero_identificacion: str) -> str:
    if not username or not email or not password:
        return "Usuario, correo y contraseña son obligatorios."
    if not is_valid_email(email):
        return "Formato de correo inválido. Usa un correo válido (ej: usuario@dominio.com)."
    if numero_identificacion and not is_valid_cedula(numero_identificacion):
        return "Formato de cédula inválido. Debe contener solo números (6 a 12 dígitos)."
    if len(password) < 6:
        return "La contraseña debe tener al menos 6 caracteres."
    if password != confirm_password:
        return "La confirmación de contraseña no coincide."
    return ""


def _validate_self_register_role(selected_role: str) -> str:
    allowed_self_roles = {"estudiante_udec", "docente_udec", "funcionario_area", "vigilante"}
    if selected_role not in allowed_self_roles:
        return "El rol seleccionado no es valido para auto-registro."
    return ""


def _validate_register_uniqueness(username: str, email: str) -> str:
    try:
        existing_user = User.get_by_username(username)
    except Exception as exc:
        return f"No se pudo validar el usuario: {exc}"

    if existing_user:
        return "El nombre de usuario ya está en uso."

    try:
        existing_email = User.get_by_email(email)
    except Exception:
        existing_email = None

    if existing_email:
        return "El correo ya está registrado."

    return ""


@auth_bp.get("/login")
def login():
    # Si ya inició sesión, no mostrar login de nuevo.
    if current_user.is_authenticated:
        return redirect(url_for(DASHBOARD_ROUTE))
    return render_template("login.html")


@auth_bp.post("/login")
def login_post():
    # Lee datos del formulario.
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "").strip()

    # Busca usuario y valida credenciales.
    try:
        user = User.get_by_username(username)
    except Exception as exc:
        flash(f"Error de conexion a BD: {exc}", "error")
        return redirect(url_for(LOGIN_ROUTE))

    if not user or not user.verify_password(password):
        flash("Credenciales invalidas.", "error")
        return redirect(url_for(LOGIN_ROUTE))

    # Crea sesión activa.
    login_user(user)
    flash(f"Inicio de sesion exitoso. Rol detectado: {_role_label(getattr(user, 'rol', ''))}.", "success")
    return redirect(url_for(DASHBOARD_ROUTE))


@auth_bp.get("/register")
def register():
    if current_user.is_authenticated:
        return redirect(url_for(DASHBOARD_ROUTE))
    return render_template("auth/register.html")


@auth_bp.post("/register")
def register_post():
    if current_user.is_authenticated:
        return redirect(url_for(DASHBOARD_ROUTE))

    username = (request.form.get("username", "") or "").strip()
    email = normalize_email(request.form.get("email", ""))
    password = (request.form.get("password", "") or "").strip()
    confirm_password = (request.form.get("confirm_password", "") or "").strip()
    nombre = (request.form.get("nombre", "") or "").strip()
    apellido = (request.form.get("apellido", "") or "").strip()
    numero_identificacion = normalize_cedula(request.form.get("numero_identificacion", ""))
    selected_role = normalize_role(request.form.get("role", "estudiante_udec"))

    input_error = _validate_register_input(
        username=username,
        email=email,
        password=password,
        confirm_password=confirm_password,
        numero_identificacion=numero_identificacion,
    )
    if input_error:
        flash(input_error, "error")
        return redirect(url_for(REGISTER_ROUTE))

    role_error = _validate_self_register_role(selected_role)
    if role_error:
        flash(role_error, "error")
        return redirect(url_for(REGISTER_ROUTE))

    uniqueness_error = _validate_register_uniqueness(username=username, email=email)
    if uniqueness_error:
        flash(uniqueness_error, "error")
        return redirect(url_for(REGISTER_ROUTE))

    try:
        User.create_user(
            username=username,
            raw_password=password,
            role=selected_role,
            estado="activo",
            nombre=nombre,
            apellido=apellido,
            email=email,
            numero_identificacion=numero_identificacion,
        )
    except Exception as exc:
        flash(f"No se pudo crear la cuenta: {exc}", "error")
        return redirect(url_for(REGISTER_ROUTE))

    flash(f"Cuenta creada correctamente con rol {_role_label(selected_role)}. Ya puedes iniciar sesion.", "success")
    return redirect(url_for(LOGIN_ROUTE))


@auth_bp.get("/logout")
def logout():
    # Cierra sesión actual.
    logout_user()
    flash("Sesion cerrada.", "success")
    return redirect(url_for(LOGIN_ROUTE))


@auth_bp.get("/forgot-password")
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for(DASHBOARD_ROUTE))
    return render_template("auth/forgot_password.html")


@auth_bp.post("/forgot-password")
def forgot_password_post():
    email = normalize_email(request.form.get("email", ""))
    if not email:
        flash("Debes ingresar el correo registrado.", "error")
        return redirect(url_for(FORGOT_PASSWORD_ROUTE))

    if not is_valid_email(email):
        flash("Formato de correo inválido. Usa un correo válido (ej: usuario@dominio.com).", "error")
        return redirect(url_for(FORGOT_PASSWORD_ROUTE))

    user = User.get_by_email(email)
    # Mensaje genérico por seguridad para no revelar usuarios existentes.
    generic_message = "Si el correo está registrado, recibirás un enlace para restablecer la contraseña."

    if not user:
        flash(generic_message, "success")
        return redirect(url_for(LOGIN_ROUTE))

    token = _generate_reset_token(email)
    reset_link = url_for(RESET_PASSWORD_ROUTE, token=token, _external=True)

    try:
        was_sent = _send_password_reset_email(to_email=email, reset_link=reset_link)
    except Exception as exc:
        flash(f"No se pudo enviar el correo de recuperación: {exc}", "error")
        return redirect(url_for(FORGOT_PASSWORD_ROUTE))

    if not was_sent:
        flash(f"[PRUEBA] Enlace de recuperación: {reset_link}", "warning")

    flash(generic_message, "success")
    return redirect(url_for(LOGIN_ROUTE))


@auth_bp.get("/reset-password/<token>")
def reset_password(token: str):
    if current_user.is_authenticated:
        return redirect(url_for(DASHBOARD_ROUTE))

    email = _verify_reset_token(token)
    if not email:
        flash("El enlace de recuperación es inválido o expiró.", "error")
        return redirect(url_for(FORGOT_PASSWORD_ROUTE))

    return render_template("auth/reset_password.html", token=token)


@auth_bp.post("/reset-password/<token>")
def reset_password_post(token: str):
    if current_user.is_authenticated:
        return redirect(url_for(DASHBOARD_ROUTE))

    email = _verify_reset_token(token)
    if not email:
        flash("El enlace de recuperación es inválido o expiró.", "error")
        return redirect(url_for(FORGOT_PASSWORD_ROUTE))

    password = (request.form.get("password", "") or "").strip()
    confirm_password = (request.form.get("confirm_password", "") or "").strip()

    if len(password) < 6:
        flash("La nueva contraseña debe tener al menos 6 caracteres.", "error")
        return redirect(url_for(RESET_PASSWORD_ROUTE, token=token))

    if password != confirm_password:
        flash("La confirmación de contraseña no coincide.", "error")
        return redirect(url_for(RESET_PASSWORD_ROUTE, token=token))

    user = User.get_by_email(email)
    if not user:
        flash("No se encontró el usuario asociado al enlace de recuperación.", "error")
        return redirect(url_for(FORGOT_PASSWORD_ROUTE))

    try:
        User.update_password(user_id=int(user.id), raw_password=password)
    except Exception as exc:
        flash(f"No se pudo actualizar la contraseña: {exc}", "error")
        return redirect(url_for(RESET_PASSWORD_ROUTE, token=token))

    flash("Contraseña actualizada correctamente. Ahora puedes iniciar sesión.", "success")
    return redirect(url_for(LOGIN_ROUTE))

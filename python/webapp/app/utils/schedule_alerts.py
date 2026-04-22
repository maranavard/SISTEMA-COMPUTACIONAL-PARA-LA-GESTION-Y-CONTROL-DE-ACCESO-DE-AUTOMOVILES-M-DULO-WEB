"""Alertas de operación para horarios especiales (domingo/festivo)."""

from __future__ import annotations

import smtplib
from email.message import EmailMessage

from flask import current_app

from app.models.user import User


def _admin_recipients() -> list[str]:
    recipients: list[str] = []
    allowed = {"admin_sistema", "admin", "administrador"}

    for user in User.list_users():
        rol = (str(user.get("rol") or "")).strip().lower()
        email = (str(user.get("email") or "")).strip()
        if rol in allowed and email and email not in recipients:
            recipients.append(email)

    return recipients


def send_admin_offday_alert(
    *,
    placa: str,
    actor_username: str,
    reason: str,
    fecha_hora_text: str,
) -> bool:
    recipients = _admin_recipients()
    if not recipients:
        return False

    host = (current_app.config.get("MAIL_HOST") or "").strip()
    user = (current_app.config.get("MAIL_USER") or "").strip()
    password = current_app.config.get("MAIL_PASSWORD") or ""
    port = int(current_app.config.get("MAIL_PORT") or 587)
    use_tls = bool(current_app.config.get("MAIL_USE_TLS"))
    sender = (current_app.config.get("MAIL_FROM") or user).strip()
    suppress_send = bool(current_app.config.get("MAIL_SUPPRESS_SEND"))

    if suppress_send:
        print(
            "[ALERTA-HORARIO-TEST] "
            f"Placa={placa}, usuario={actor_username}, motivo={reason}, fecha={fecha_hora_text}, "
            f"destinatarios={','.join(recipients)}"
        )
        return False

    if not host or not user or not password or not sender:
        print(
            "[ALERTA-HORARIO-TEST] SMTP incompleto. "
            f"Placa={placa}, usuario={actor_username}, motivo={reason}, fecha={fecha_hora_text}, "
            f"destinatarios={','.join(recipients)}"
        )
        return False

    msg = EmailMessage()
    msg["Subject"] = "Alerta: Registro de vehículo en día/horario no operativo"
    msg["From"] = sender
    msg["To"] = ", ".join(recipients)
    msg.set_content(
        "Se registró un vehículo en una condición no operativa definida por el sistema.\n\n"
        f"Placa: {placa}\n"
        f"Usuario: {actor_username}\n"
        f"Motivo: {reason}\n"
        f"Fecha y hora: {fecha_hora_text}\n"
    )

    with smtplib.SMTP(host, port, timeout=20) as server:
        if use_tls:
            server.starttls()
        server.login(user, password)
        server.send_message(msg)

    return True
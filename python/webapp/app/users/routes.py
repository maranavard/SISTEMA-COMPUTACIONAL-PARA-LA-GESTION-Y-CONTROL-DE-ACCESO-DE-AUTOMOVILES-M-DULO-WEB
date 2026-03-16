"""Módulo CRUD de usuarios (Sprint 1)."""

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required

from app.models.user import User
from app.utils.authz import admin_required


users_bp = Blueprint("users", __name__, url_prefix="/usuarios")


@users_bp.get("/")
@login_required
@admin_required
def list_users():
    users = User.list_users()
    return render_template("users/index.html", users=users)


@users_bp.post("/crear")
@login_required
@admin_required
def create_user():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "").strip()
    role = request.form.get("role", "conductor_udec").strip() or "conductor_udec"
    estado = request.form.get("estado", "activo").strip() or "activo"
    nombre = request.form.get("nombre", "").strip()
    apellido = request.form.get("apellido", "").strip()
    email = request.form.get("email", "").strip()
    numero_identificacion = request.form.get("numero_identificacion", "").strip()

    if not username or not password or not email:
        flash("Usuario, correo institucional y contraseña son obligatorios.", "error")
        return redirect(url_for("users.list_users"))

    try:
        User.create_user(
            username=username,
            raw_password=password,
            role=role,
            estado=estado,
            nombre=nombre,
            apellido=apellido,
            email=email,
            numero_identificacion=numero_identificacion,
        )
        flash("Usuario creado correctamente.", "success")
    except Exception as exc:
        flash(f"No se pudo crear el usuario: {exc}", "error")

    return redirect(url_for("users.list_users"))


@users_bp.post("/<int:user_id>/actualizar")
@login_required
@admin_required
def update_user(user_id: int):
    role = request.form.get("role", "conductor_udec").strip() or "conductor_udec"
    estado = request.form.get("estado", "activo").strip() or "activo"
    nombre = request.form.get("nombre", "").strip()
    apellido = request.form.get("apellido", "").strip()
    email = request.form.get("email", "").strip()
    numero_identificacion = request.form.get("numero_identificacion", "").strip()
    new_password = request.form.get("new_password", "").strip()

    try:
        User.update_user(
            user_id=user_id,
            role=role,
            estado=estado,
            nombre=nombre,
            apellido=apellido,
            email=email,
            numero_identificacion=numero_identificacion,
        )
        if new_password:
            User.update_password(user_id=user_id, raw_password=new_password)
        flash("Usuario actualizado correctamente.", "success")
    except Exception as exc:
        flash(f"No se pudo actualizar el usuario: {exc}", "error")

    return redirect(url_for("users.list_users"))

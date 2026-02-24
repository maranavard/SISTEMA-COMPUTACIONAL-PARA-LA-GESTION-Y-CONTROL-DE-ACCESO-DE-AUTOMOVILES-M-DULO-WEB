from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user

from app.models.user import User


auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.get("/login")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    return render_template("login.html")


@auth_bp.post("/login")
def login_post():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "").strip()

    user = User.get_by_username(username)
    if not user or not user.verify_password(password):
        flash("Credenciales inválidas.", "error")
        return redirect(url_for("auth.login"))

    login_user(user)
    flash("Inicio de sesión exitoso.", "success")
    return redirect(url_for("main.dashboard"))


@auth_bp.get("/logout")
def logout():
    logout_user()
    flash("Sesión cerrada.", "success")
    return redirect(url_for("auth.login"))

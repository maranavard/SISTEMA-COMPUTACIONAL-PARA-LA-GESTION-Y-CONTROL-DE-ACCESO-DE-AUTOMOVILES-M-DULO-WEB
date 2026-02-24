from flask import Blueprint, redirect, render_template, url_for
from flask_login import current_user, login_required


main_bp = Blueprint("main", __name__)


@main_bp.get("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    return redirect(url_for("auth.login"))


@main_bp.get("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", user=current_user)

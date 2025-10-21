from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user
from src.infrastructure.persistence.database import db
from src.infrastructure.persistence.database import db
from src.infrastructure.persistence.repositories.user_repository import UserRepository
from src.application.use_cases.auth_service import AuthService

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.get("/login")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("tickets.dashboard"))
    return render_template("auth/login.html", title="Login")

@auth_bp.post("/login")
def login_post():
    if current_user.is_authenticated:
        return redirect(url_for("tickets.dashboard"))

    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    remember = bool(request.form.get("remember"))

    svc = AuthService(UserRepository(db.session))
    user = svc.authenticate(email, password)

    if not user:
        flash("Correo o contraseña inválidos.", "error")
        return redirect(url_for("auth.login"))

    login_user(user, remember=remember)
    return redirect(request.args.get("next") or url_for("tickets.dashboard"))

@auth_bp.post("/logout")
def logout():
    if current_user.is_authenticated:
        logout_user()
        #flash("Sesión cerrada correctamente.", "info")
    return redirect(url_for("public.index"))
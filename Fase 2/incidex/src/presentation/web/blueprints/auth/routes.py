from flask import Blueprint, render_template

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login")
def login():
    return render_template("auth/login.html", title="Iniciar sesión")

@auth_bp.route("/logout")
def logout():
    # placeholder por ahora
    return render_template("auth/login.html", title="Iniciar sesión")
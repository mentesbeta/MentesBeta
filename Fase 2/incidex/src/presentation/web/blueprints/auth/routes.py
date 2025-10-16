from flask import Blueprint, render_template

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', endpoint='login')
def login():
    return render_template('auth/login.html', title='Login')

@auth_bp.route("/logout")
def logout():
    # placeholder por ahora
    return render_template("auth/login.html", title="Iniciar sesión")
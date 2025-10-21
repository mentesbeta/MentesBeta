from flask import Flask
from dotenv import load_dotenv
import os
from datetime import timedelta

from flask_login import LoginManager
from flask_migrate import Migrate

from flask_wtf import CSRFProtect
from flask_wtf.csrf import generate_csrf

from src.infrastructure.persistence.database import db

def create_app():
    
    load_dotenv()
    app = Flask(__name__)

    app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev_secret")

    # ==== Base de datos (MySQL) ====
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_pre_ping": True,
        "pool_recycle": 280,
    }
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)

    # iniciar modelos
    import src.domain.entities 


    # ==== Migrate ====
    Migrate(app, db, compare_type=True)

    # ==== CSRF global ====
    CSRFProtect(app)

    @app.context_processor
    def inject_csrf_token():
        return {"csrf_token": generate_csrf}

    # ===== Flask-Login =====
    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.init_app(app)

    from src.domain.entities.user import User

    @login_manager.user_loader
    def load_user(user_id: str):
        # MySQL autoincrement INT
        try:
            return db.session.get(User, int(user_id))
        except Exception:
            return None

    # ==== Tiempo de sesión persistente (remember me) ====
    app.config["REMEMBER_COOKIE_DURATION"] = timedelta(days=int(os.getenv("REMEMBER_COOKIE_DURATION_DAYS", "7")))

    # ===== Blueprints =====
    from src.presentation.web.blueprints.public.routes import public_bp
    app.register_blueprint(public_bp)

    from src.presentation.web.blueprints.tickets.routes import tickets
    app.register_blueprint(tickets)

    from src.presentation.web.blueprints.auth.routes import auth_bp
    app.register_blueprint(auth_bp)

    # ==== Comandos CLI personalizados ====
    from src.commands.seed_user import create_user_cmd
    app.cli.add_command(create_user_cmd)

    @app.route("/health")
    def health_check():
        return {"status": "ok", "service": "Incidex Web"}

    return app
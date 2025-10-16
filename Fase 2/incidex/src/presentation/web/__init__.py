from flask import Flask
from dotenv import load_dotenv
import os
from flask_login import LoginManager

def create_app():
    load_dotenv()
    app = Flask(__name__)
    app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev_secret")

    # ===== Flask-Login: inicialización mínima =====
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'   # endpoint a donde redirigiría si usas @login_required
    login_manager.init_app(app)

    # Loader de usuario (stub). Cuando tengas tu modelo User, cámbialo:
    @login_manager.user_loader
    def load_user(user_id: str):
        # TODO: retornar objeto User desde DB por ID. Por ahora, no hay usuarios.
        return None

    # ===== Blueprints =====
    from src.presentation.web.blueprints.public.routes import public_bp
    app.register_blueprint(public_bp)

    from src.presentation.web.blueprints.tickets.routes import tickets
    app.register_blueprint(tickets)

    from src.presentation.web.blueprints.auth.routes import auth_bp
    app.register_blueprint(auth_bp)

    # ===== current_user para plantillas (fallback seguro) =====
    # Si Flask-Login está activo, inyecta el real; si no, inyecta uno anónimo.
    class _Anon:
        is_authenticated = False
        name = None

    @app.context_processor
    def inject_current_user():
        try:
            from flask_login import current_user as cu
            return {'current_user': cu}
        except Exception:
            return {'current_user': _Anon()}

    @app.route("/health")
    def health_check():
        return {"status": "ok", "service": "Incidex Web"}

    return app
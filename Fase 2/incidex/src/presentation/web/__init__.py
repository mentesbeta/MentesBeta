from flask import Flask
from dotenv import load_dotenv
import os

def create_app():
    """Crea e inicializa la aplicación Flask."""
    load_dotenv()  # carga las variables de entorno desde .env

    app = Flask(__name__)
    app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev_secret")

    # Registro de blueprints
    from src.presentation.web.blueprints.public.routes import public_bp
    app.register_blueprint(public_bp)

    @app.route("/health")
    def health_check():
        return {"status": "ok", "service": "Incidex Web"}

    return app

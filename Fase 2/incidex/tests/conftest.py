# tests/conftest.py
import os
os.environ.setdefault("GEMINI_API_KEY", "dummy")
import pytest
import datetime
import uuid

from src.presentation.web import create_app
from src.infrastructure.persistence.database import db
from src.domain.entities.user import User


@pytest.fixture
def app():
    os.environ["FLASK_ENV"] = "testing"
    os.environ["FLASK_DEBUG"] = "0"

    app = create_app()
    app.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=False,
    )
    return app


@pytest.fixture
def test_user(app):
    """
    Usa un usuario de prueba si ya existe; si no, lo crea.
    """
    fecha_actual = datetime.date.today()
    fecha_especifica = datetime.date(1990, 1, 1)

    with app.app_context():
        # 1) ¿Ya existe?
        user = User.query.filter_by(email="test@example.com").first()
        if user:
            return user.id

        # 2) Si no existe, lo creamos
        user = User(
            names_worker="Usuario",
            last_name="Prueba",
            birthdate=fecha_especifica,
            email="test@example.com",
            gender="M",
            password_hash="admin",
            department_id=1,
            created_at=fecha_actual,
            updated_at=fecha_actual,
            is_active=1,
        )
        db.session.add(user)
        db.session.commit()
        return user.id



@pytest.fixture
def auth_client(app, test_user):
    """
    Client con usuario YA logueado (usando el id del fixture test_user).
    """
    client = app.test_client()

    with client.session_transaction() as sess:
        sess["_user_id"] = str(test_user) 
        sess["_fresh"] = True

    return client


@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def db_conn(app):
    """
    Entrega una conexión cruda a la BD (DB-API) usando el engine de SQLAlchemy.
    Se hace rollback al final del test para no dejar datos sucios.
    """
    with app.app_context():
        conn = db.engine.raw_connection()  # conexión real al MySQL de Docker
        conn.autocommit = False

        try:
            yield conn
            conn.rollback()  # revertimos todo lo hecho en el test
        finally:
            conn.close()

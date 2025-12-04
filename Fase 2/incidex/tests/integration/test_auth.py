from http import HTTPStatus
import pytest


# 1) GET /auth/login
def test_login_get(client):
    """
    La página de login se puede ver sin estar autenticado.
    """
    resp = client.get("/auth/login")
    assert resp.status_code == HTTPStatus.OK
    # Algo muy genérico pero útil: debería haber un <form>
    assert b"<form" in resp.data


# 2) POST /auth/login OK
def test_login_post_ok(client, monkeypatch, test_user):
    """
    Login con credenciales válidas:
    - Parcheamos AuthService.authenticate para que devuelva el usuario de prueba.
    - Debe redirigir al dashboard (/app/dashboard).
    """

    def fake_auth(self, email, password):
        # Buscamos el usuario real en la BD por email (el fixture ya lo creó)
        from src.domain.entities.user import User
        from src.infrastructure.persistence.database import db

        return db.session.query(User).filter_by(email=email).first()

    # Parcheamos el método authenticate del servicio
    monkeypatch.setattr(
        "src.application.use_cases.auth_service.AuthService.authenticate",
        fake_auth,
    )

    form_data = {
        "email": "test@example.com",   # mismo mail que usa tu fixture test_user
        "password": "cualquier-clave",
    }

    resp = client.post("/auth/login", data=form_data, follow_redirects=False)

    # Debe hacer redirect al dashboard
    assert resp.status_code == HTTPStatus.FOUND  # 302
    location = resp.headers.get("Location", "")
    assert "/app/dashboard" in location


# 3) POST /auth/login FAIL
def test_login_post_fail(client, monkeypatch, test_user):
    """
    Login con credenciales inválidas:
    - AuthService.authenticate devuelve None.
    - Debe redirigir de vuelta a /auth/login y seguir sin poder entrar al dashboard.
    """

    # Forzamos fallo de autenticación
    def fake_auth(self, email, password):
        return None

    monkeypatch.setattr(
        "src.application.use_cases.auth_service.AuthService.authenticate",
        fake_auth,
    )

    form_data = {
        "email": "test@example.com",
        "password": "clave-incorrecta",
    }

    # Tu código actual hace redirect de vuelta a login cuando falla
    resp = client.post("/auth/login", data=form_data, follow_redirects=False)
    assert resp.status_code == HTTPStatus.FOUND  # 302
    assert "/auth/login" in resp.headers.get("Location", "")

    # Extra: confirmamos que SIGUE sin estar logueado intentando entrar al dashboard
    resp2 = client.get("/app/dashboard", follow_redirects=False)
    assert resp2.status_code == HTTPStatus.FOUND  # 302
    assert "/auth/login" in resp2.headers.get("Location", "")


# 4) LOGOUT
def test_logout(auth_client):
    """
    Logout:
    - Con un usuario ya autenticado (auth_client)
    - POST /auth/logout debe cerrar la sesión y redirigir.
    - Luego, intentar entrar al dashboard debe volver a pedir login.
    """

    # 1) Hacemos logout
    resp = auth_client.post("/auth/logout", follow_redirects=False)
    assert resp.status_code == HTTPStatus.FOUND  # 302

    # 2) Ahora ya NO debería poder entrar al dashboard sin ser redirigido a login
    resp2 = auth_client.get("/app/dashboard", follow_redirects=False)
    assert resp2.status_code == HTTPStatus.FOUND
    assert "/auth/login" in resp2.headers.get("Location", "")

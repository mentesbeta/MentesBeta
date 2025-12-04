import pytest
from http import HTTPStatus

# Estas rutas son privadas (Blueprint "tickets" con prefix /app)
PRIVATE_PATHS = [
    "/app/dashboard",
    "/app/tickets/create",
    "/app/mine",
]


@pytest.mark.parametrize("path", PRIVATE_PATHS)
def test_private_routes_require_login(client, path):
    """
    Todas las rutas privadas deben redirigir a /auth/login
    cuando el usuario NO está autenticado.
    """
    resp = client.get(path, follow_redirects=False)

    # Flask-Login responde 302 hacia login_view
    assert resp.status_code in (302, 303)

    # Debe incluir la ruta de login en el Location
    location = resp.headers.get("Location", "")
    assert "/auth/login" in location

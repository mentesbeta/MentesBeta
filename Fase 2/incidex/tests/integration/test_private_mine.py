# tests/integration/test_private_mine.py

from http import HTTPStatus


def test_mine_ok_when_logged_in(auth_client, monkeypatch):
    """
    Caso base: usuario autenticado sin rol especial (no ADMIN ni ANALYST).
    Debe ver la página 'Mis Tickets (creados o asignados)' y
    la vista debe llamar a TicketService.scoped_list.
    """

    called = {}

    def fake_scoped_list(self, user_id, roles, **kwargs):
        # Guardamos los argumentos que recibió el método
        called["user_id"] = user_id
        called["roles"] = roles
        called["kwargs"] = kwargs

        # Devolvemos un resultado mínimo válido para que el template no explote
        return {
            "items": [],
            "total": 0,
            "page": 1,
            "pages": 1,
            "per_page": 10,
            "filters": {
                "q": "",
                "status_id": None,
                "priority_id": None,
                "category_id": None,
                "from": "",
                "to": "",
            },
            "catalogs": {
                "statuses": [],
                "priorities": [],
                "categories": [],
            },
        }

    # Parcheamos solo el método scoped_list usado en la ruta /app/mine
    monkeypatch.setattr(
        "src.presentation.web.blueprints.tickets.routes.TicketService.scoped_list",
        fake_scoped_list,
    )

    resp = auth_client.get("/app/mine")
    assert resp.status_code == HTTPStatus.OK

    html = resp.data.decode("utf-8")

    # Para un usuario normal (sin ADMIN / ANALYST) el título debe ser:
    # "Mis Tickets"
    assert "Mis Tickets" in html

    # Verificamos que nuestra función fake fue llamada
    assert "user_id" in called
    assert called["user_id"] is not None

    # roles debería ser una lista (lo que leas en la vista desde current_user.roles)
    assert isinstance(called["roles"], list)


def test_mine_filters_are_passed_to_scoped_list(auth_client, monkeypatch):
    """
    Comprobamos que los parámetros de filtro del query string
    se pasen correctamente a scoped_list.
    """

    called = {}

    def fake_scoped_list(self, user_id, roles, **kwargs):
        called["kwargs"] = kwargs
        return {
            "items": [],
            "total": 0,
            "page": kwargs.get("page", 1),
            "pages": 1,
            "per_page": kwargs.get("per_page", 10),
            "filters": {},
            "catalogs": {},
        }

    monkeypatch.setattr(
        "src.presentation.web.blueprints.tickets.routes.TicketService.scoped_list",
        fake_scoped_list,
    )

    resp = auth_client.get(
        "/app/mine?q=INC-00001&status_id=1&priority_id=2&category_id=3"
        "&from=2025-01-01&to=2025-12-31&page=2&per_page=20"
    )

    assert resp.status_code == HTTPStatus.OK
    assert "kwargs" in called

    kwargs = called["kwargs"]

    assert kwargs["q"] == "INC-00001"
    assert kwargs["status_id"] == 1
    assert kwargs["priority_id"] == 2
    assert kwargs["category_id"] == 3
    assert kwargs["date_from"] == "2025-01-01"
    assert kwargs["date_to"] == "2025-12-31"
    assert kwargs["page"] == 2
    assert kwargs["per_page"] == 20

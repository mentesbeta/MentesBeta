from http import HTTPStatus
import uuid

from src.infrastructure.persistence.database import db
from src.domain.entities.user import User
from src.domain.entities.ticket import Ticket
from src.infrastructure.persistence.repositories.ticket_repository import TicketRepository




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


def _create_ticket(
    app,
    *,
    requester_id: int,
    assignee_id: int | None = None,
    title: str = "Ticket de prueba mine",
) -> Ticket:
    """
    Helper para crear un ticket asociado al usuario de pruebas.
    Usa un code único para evitar choques en la BD.
    """
    with app.app_context():
        repo = TicketRepository()
        status_nuevo_id = repo.get_status_id_by_name("NUEVO")
        if status_nuevo_id is None:
            status_nuevo_id = 1  # fallback por si acaso

        code = f"INC-{uuid.uuid4().hex[:8].upper()}"

        t = Ticket(
            code=code,
            title=title,
            description="Detalle de prueba mine",
            requester_id=requester_id,
            assignee_id=assignee_id,
            department_id=1,
            category_id=1,
            priority_id=1,
            status_id=status_nuevo_id,
        )
        db.session.add(t)
        db.session.commit()
        # refrescamos para asegurarnos que tiene id
        db.session.refresh(t)
        return t


def test_mine_shows_tickets_for_requester(auth_client, app):
    """
    /app/mine debe listar los tickets donde el usuario es requester o assignee.
    Aquí probamos que, siendo requester, vea sus tickets.
    """
    with app.app_context():
        user = db.session.query(User).filter_by(email="test@example.com").first()
        assert user is not None
        requester_id = user.id

        _create_ticket(app, requester_id=requester_id, assignee_id=None,
                       title="Ticket mine 1")
        _create_ticket(app, requester_id=requester_id, assignee_id=None,
                       title="Ticket mine 2")

    # Forzamos per_page bien grande para que solo haya 1 página
    resp = auth_client.get("/app/mine?per_page=1000")

    assert resp.status_code == HTTPStatus.OK
    html = resp.data.decode("utf-8")
    assert "Ticket mine 1" in html
    assert "Ticket mine 2" in html



def test_mine_filter_by_q_code(auth_client, app):
    """
    /app/mine?q=<code> debe filtrar por código exacto o título (según tu lógica).
    Probamos que al buscar por el code de un ticket, no aparezca otro.
    """
    with app.app_context():
        user = db.session.query(User).filter_by(email="test@example.com").first()
        assert user is not None
        requester_id = user.id

        t1 = _create_ticket(app, requester_id=requester_id, assignee_id=None,
                            title="Ticket filtro 1")
        t2 = _create_ticket(app, requester_id=requester_id, assignee_id=None,
                            title="Ticket filtro 2")

    # Buscamos por el código de t1
    resp = auth_client.get(f"/app/mine?q={t1.code}")
    assert resp.status_code == HTTPStatus.OK

    html = resp.data.decode("utf-8")
    # Debe estar t1 pero no t2
    assert t1.code in html
    assert "Ticket filtro 1" in html

    assert t2.code not in html
    assert "Ticket filtro 2" not in html

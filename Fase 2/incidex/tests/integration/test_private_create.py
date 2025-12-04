# tests/integration/test_private_create.py
from http import HTTPStatus
from types import SimpleNamespace
from http import HTTPStatus

def test_create_get_ok(auth_client):
    """
    Un usuario logueado debe poder ver el formulario de creación de ticket.
    """
    resp = auth_client.get("/app/tickets/create")
    assert resp.status_code == HTTPStatus.OK

    html = resp.data.decode("utf-8")
    # Ajusta el texto si tu template tiene otro título
    assert "Crear Ticket" in html

from types import SimpleNamespace
from http import HTTPStatus


def test_create_post_happy_path(auth_client, monkeypatch):
    """
    Crea un ticket básico y verifica que:
    - Se llama a TicketService.create con los parámetros correctos
    - Se autoasigna al analista con menor carga para el departamento
    - Redirige al detalle del ticket creado
    """

    called = {}

    def fake_create(
        self,
        *,
        requester_id,
        subject,
        details,
        category_id,
        department_id,
        priority_id,
        assignee_id=None,
    ):
        called["requester_id"] = requester_id
        called["subject"] = subject
        called["details"] = details
        called["category_id"] = category_id
        called["department_id"] = department_id
        called["priority_id"] = priority_id
        called["assignee_id"] = assignee_id

        # Simulamos CreatedTicket(id=123, code="INC-00123")
        return SimpleNamespace(id=123, code="INC-00123")

    # Simulamos que para el depto 2 hay un analista con id 42
    def fake_analysts_by_dept_map(self):
        return {
            2: [
                {"id": 42, "full_name": "Analista Test", "load": 3},
            ]
        }

    # Parcheamos el mapa de analistas (lo usa create_post para autoasignar)
    monkeypatch.setattr(
        "src.presentation.web.blueprints.tickets.routes.TicketService.analysts_by_dept_map",
        fake_analysts_by_dept_map,
    )

    # Parcheamos SOLO el método create usado en la ruta /app/create
    monkeypatch.setattr(
        "src.presentation.web.blueprints.tickets.routes.TicketService.create",
        fake_create,
    )

    form_data = {
        "subject": "Error en login",
        "details": "No puedo entrar con mi usuario.",
        "category_id": "1",
        "department_id": "2",  # importante: coincide con el fake_analysts_by_dept_map
        "priority_id": "3",
        "assignee_id": "",  # vacío → backend debería autoasignar a 42
    }

    resp = auth_client.post("/app/create", data=form_data, follow_redirects=False)

    # Debe redirigir al detalle
    assert resp.status_code == HTTPStatus.FOUND  # 302
    assert "/app/detail/123" in resp.headers["Location"]

    # Verificamos que se llamó a create con los datos del form
    assert called  # no vacío
    assert called["subject"] == form_data["subject"]
    assert called["details"] == form_data["details"]
    assert called["category_id"] == int(form_data["category_id"])
    assert called["department_id"] == int(form_data["department_id"])
    assert called["priority_id"] == int(form_data["priority_id"])

    # Como tenemos analistas en el depto 2, debe autoasignar al 42
    assert called["assignee_id"] == 42

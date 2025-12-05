from http import HTTPStatus
from src.infrastructure.persistence.database import db
from src.domain.entities.ticket import Ticket
from src.domain.entities.user import User
import uuid


def test_full_flow(auth_client, app):
    """
    Flujo E2E:
    1. Usuario logueado crea ticket
    2. Accede a /mine y lo ve
    3. Entra al detalle y aparece el título
    """

    # 1) Crear ticket vía POST
    code = f"INC-{uuid.uuid4().hex[:6]}"
    form_data = {
        "subject": "E2E test",
        "details": "Flujo completo",
        "category_id": "1",
        "department_id": "1",
        "priority_id": "1",
        "assignee_id": "",
    }

    resp = auth_client.post("/app/create", data=form_data, follow_redirects=False)
    assert resp.status_code == HTTPStatus.FOUND

    # obtener ID desde /detail/<id>
    detail_url = resp.headers["Location"]
    ticket_id = int(detail_url.split("/")[-1])

    # 2) /mine debe verlo
    resp2 = auth_client.get("/app/mine?per_page=500")
    assert resp2.status_code == 200
    html = resp2.data.decode()
    assert "E2E test" in html

    # 3) /detail/<id> debe mostrarlo
    resp3 = auth_client.get(detail_url)
    html2 = resp3.data.decode()
    assert "Flujo completo" in html2

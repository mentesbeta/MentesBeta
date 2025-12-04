from http import HTTPStatus

from src.infrastructure.persistence.database import db
from src.domain.entities.ticket import Ticket
from src.domain.entities.user import User

import uuid


def test_detail_ok_for_requester(auth_client, app):
    """
    Crea un ticket en BD para el usuario de prueba
    y verifica que /app/detail/<id> responde 200 y muestra los datos.
    """

    with app.app_context():
        # Tomamos el usuario de prueba que ya se crea en el fixture test_user
        user = db.session.query(User).filter_by(email="test@example.com").first()
        assert user is not None
        requester_id = user.id

        unique_code = f"INC-{uuid.uuid4().hex[:8].upper()}"

        # Creamos un ticket mínimo válido
        t = Ticket(
            code = unique_code,
            title="Ticket prueba detalle",
            description="Detalle de prueba",
            requester_id=requester_id,
            assignee_id=None,
            department_id=1,
            category_id=1,
            priority_id=1,
            status_id=1,  
        )
        db.session.add(t)
        db.session.commit()
        ticket_id = t.id

    # Ahora, como auth_client ya está logueado con el test_user,
    # hacemos GET al detalle
    resp = auth_client.get(f"/app/detail/{ticket_id}")

    assert resp.status_code == HTTPStatus.OK
    # El título debería aparecer en el HTML
    assert "Ticket prueba detalle".encode("utf-8") in resp.data
    # Y el código también
    assert unique_code.encode("utf-8") in resp.data
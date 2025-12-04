from http import HTTPStatus

from src.infrastructure.persistence.database import db
from src.infrastructure.persistence.repositories.ticket_repository import TicketRepository
from src.domain.entities.ticket import Ticket
from src.domain.entities.user import User

import uuid

def test_change_status_assignee_to_en_progreso_ok(auth_client, app):
    """
    Caso feliz:
    - El usuario de prueba es el solicitante y ASIGNADO del ticket.
    - Hace POST a /app/detail/<id>/status con estado EN_PROGRESO.
    - Debe:
        * responder 302 (redirect al detalle)
        * actualizar el status_id del ticket en BD a EN_PROGRESO
    """

    with app.app_context():
        # 1) Buscamos el usuario de prueba que crea el fixture test_user
        user = db.session.query(User).filter_by(email="test@example.com").first()
        assert user is not None
        user_id = user.id

        # 2) Obtenemos los IDs reales de los estados desde la BD
        repo = TicketRepository()
        status_nuevo_id = repo.get_status_id_by_name("NUEVO")
        status_en_progreso_id = repo.get_status_id_by_name("EN_PROGRESO")

        # Si algo está mal seedado en la BD, queremos que el test lo grite
        assert status_nuevo_id is not None
        assert status_en_progreso_id is not None

        unique_code = f"INC-{uuid.uuid4().hex[:8].upper()}"

        # 3) Creamos un ticket donde el usuario es requester y assignee
        t = Ticket(
            code= unique_code,
            title="Ticket cambio de estado",
            description="Probar cambio a EN_PROGRESO",
            requester_id=user_id,
            assignee_id=user_id,   # MUY importante: es el asignado
            department_id=1,
            category_id=1,
            priority_id=1,
            status_id=status_nuevo_id,
        )
        db.session.add(t)
        db.session.commit()
        ticket_id = t.id

    # 4) Hacemos el POST al endpoint de cambio de estado
    resp = auth_client.post(
        f"/app/detail/{ticket_id}/status",
        data={
            "to_status_id": status_en_progreso_id,
            "note": "Comenzando a trabajar en el ticket.",
        },
        follow_redirects=False,
    )

    # Debe redirigir al detalle
    assert resp.status_code == HTTPStatus.FOUND
    assert f"/app/detail/{ticket_id}" in resp.headers.get("Location", "")

    # 5) Confirmamos en BD que el estado cambió a EN_PROGRESO
    with app.app_context():
        refreshed = db.session.get(Ticket, ticket_id)
        assert refreshed is not None
        assert refreshed.status_id == status_en_progreso_id

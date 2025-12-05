from src.application.use_cases.ticket_service import TicketService


def test_change_status_requester_can_resolve():
    class FakeRepo:
        def __init__(self):
            self.updated = False

        def get_ticket_minimal(self, ticket_id):
            return {
                "id": ticket_id,
                "requester_id": 10,
                "assignee_id": None,
                "status_id": 1,
                "department_id": 2
            }

        def get_status_name(self, status_id):
            return "RESUELTO"

        def update_status_with_history(self, ticket_id, to_status_id, actor_user_id, note):
            self.updated = True

        # para autoasignación cuando pasa a RESUELTO
        def get_least_busy_analyst_by_department(self, dept):
            return {"id": 99}

        def update_assignee_with_history(self, ticket_id, new_assignee_id, actor_user_id, note):
            self.assigned = new_assignee_id

    repo = FakeRepo()
    svc = TicketService(repo)

    svc.change_status(
        ticket_id=1,
        actor_id=10,              # REQUESTER
        actor_roles=["REQUESTER"],
        to_status_id=5,           # RESUELTO
        note="Listo!"
    )

    assert repo.updated is True
    assert repo.assigned == 99   # auto asignado a analista

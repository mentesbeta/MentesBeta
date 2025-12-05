from src.application.use_cases.ticket_service import TicketService, AISuggestion


class FakeRepo:
    def get_categories(self):
        return [{"id": 1, "name": "Software"}]

    def get_priorities(self):
        return [{"id": 1, "name": "Alta"}]

    def get_departments(self):
        return [{"id": 2, "name": "TI"}]


def fake_suggest_ticket_metadata(title, description, categories, priorities, departments):
    return {
        "category_id": 1,
        "priority_id": 1,
        "department_id": 2,
        "reason": "Coincide con términos técnicos"
    }


def test_ai_suggest_metadata(monkeypatch):
    # parchear la IA
    monkeypatch.setattr(
        "src.application.use_cases.ticket_service.suggest_ticket_metadata",
        fake_suggest_ticket_metadata
    )

    svc = TicketService(FakeRepo())
    result = svc.ai_suggest_metadata("Error app", "Falla en software")

    assert isinstance(result, AISuggestion)
    assert result.category_id == 1
    assert result.priority_id == 1
    assert result.department_id == 2
    assert "técnicos" in result.reason

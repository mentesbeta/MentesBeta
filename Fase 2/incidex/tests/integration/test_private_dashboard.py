
def test_dashboard_ok_when_logged_in(auth_client):
    """
    El dashboard privado debe cargar bien cuando hay un usuario logueado.
    """
    resp = auth_client.get("/app/dashboard")
    assert resp.status_code == 200

    html = resp.data.decode("utf-8")

    assert "Mis Tickets" in html
    assert "Nuevo Ticket" in html


def test_dashboard_shows_no_error_when_no_tickets(auth_client):
    """
    Aunque el usuario no tenga tickets, el dashboard no debe explotar.
    Solo verificamos que devuelve 200 y contiene algo del layout.
    """
    resp = auth_client.get("/app/dashboard")
    assert resp.status_code == 200
    html = resp.data.decode("utf-8")

    assert "Últimos tickets" in html or "Mis últimos tickets" in html

def test_dashboard_usa_servicio_dashboard_data(auth_client, monkeypatch):
    """
    Verificamos que la vista del dashboard llame al método
    TicketService.dashboard_data con el user_id correcto.
    """
    called = {}

    def fake_dashboard_data(self, user_id, limit=5):
        called["user_id"] = user_id
        called["limit"] = limit
        # Devolvemos una estructura mínima válida
        return {
            "kpis": {
                "open": 1,
                "in_progress": 2,
                "closed_week": 3,
            },
            "recent": [],
        }

    # Parcheamos SOLO el método dashboard_data dentro del módulo de rutas
    monkeypatch.setattr(
        "src.presentation.web.blueprints.tickets.routes.TicketService.dashboard_data",
        fake_dashboard_data,
    )

    resp = auth_client.get("/app/dashboard")
    assert resp.status_code == 200

    # Aseguramos que nuestro fake fue llamado
    assert "user_id" in called
    assert called["user_id"] is not None
    assert called["limit"] == 5
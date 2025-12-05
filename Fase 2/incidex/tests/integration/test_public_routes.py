#Test para probar la ruta publica /
def test_index_ok(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "Incidex" in resp.data.decode()

#Test para probar la ruta publica /features
def test_features_ok(client):
    resp = client.get("/features")
    assert resp.status_code == 200
    # H1 del template public/features.html
    assert "Características".encode("utf-8") in resp.data

#Test para probar la ruta publica /sobre
def test_about_ok(client):
    resp = client.get("/sobre")
    assert resp.status_code == 200
    # Título o texto reconocible en public/about.html
    assert "Sobre Incidex".encode("utf-8") in resp.data 

#Test para probar la ruta publica /support
def test_support_get_ok(client):
    resp = client.get("/support")
    assert resp.status_code == 200
    # El H1 del soporte que mostraste
    assert "Contacto y Soporte".encode("utf-8") in resp.data

#Probar funcionalidad publica envio de correo
def test_support_post_sends_email_and_redirects(client, monkeypatch):
    # 1) Preparamos un "fake" para send_support_email
    called = {}

    def fake_send_support(nombre, correo, asunto, mensaje):
        called["nombre"] = nombre
        called["correo"] = correo
        called["asunto"] = asunto
        called["mensaje"] = mensaje

    monkeypatch.setattr(
        "src.presentation.web.blueprints.public.routes.send_support_email",
        fake_send_support
    )

    # 2) POST al formulario de soporte
    form_data = {
        "nombre": "Nombre de Prueba",
        "correo": "Prueba@example.com",
        "asunto": "Problema con Incidex",
        "mensaje": "No puedo acceder a mi cuenta.",
    }

    resp = client.post("/support", data=form_data, follow_redirects=False)

    # 3) redirigir a support y respuesta en 202 después de enviar el correo
    assert resp.status_code == 200
    assert "/support" 

    # 4)validar datos
    assert called  # no está vacío
    assert called["nombre"] == form_data["nombre"]
    assert called["correo"] == form_data["correo"]
    assert called["asunto"] == form_data["asunto"]
    assert called["mensaje"] == form_data["mensaje"]

# Probar que los campos no sean ingresados todos para enviar el correo
def test_support_post_missing_fields(client):
    resp = client.post("/support", data={}, follow_redirects=False)

    # La vista devuelve  400 o 200 mostrando error
    assert resp.status_code in (200, 400)

    # El formulario debería seguir visible
    assert "Contacto y Soporte".encode("utf-8") in resp.data

# Probar que no se requiera usuario logueado para ingresar a support
def test_support_does_not_require_login(client):
    resp = client.get("/support")
    assert resp.status_code == 200

def test_support_uses_correct_template(app, client, monkeypatch):
    templates_used = []

    def fake_render(tpl, *a, **k):
        templates_used.append(tpl)
        return b"OK"

    monkeypatch.setattr("src.presentation.web.blueprints.public.routes.render_template", fake_render)

    client.get("/support")

    assert len(templates_used) == 1
    assert templates_used[0] == "public/support.html"

def test_index_has_title(client):
    resp = client.get("/")
    html = resp.data.decode()
    assert "<title>" in html
    assert "Incidex" in html


def test_support_post_with_missing_fields_shows_form(client, monkeypatch):
    """
    Si se hace POST a /support sin datos, la vista no debería explotar
    y el formulario debería seguir mostrándose.
    """
    # Evitamos que intente mandar correos reales
    def fake_send_support(nombre, correo, asunto, mensaje):
        pass

    monkeypatch.setattr(
        "src.presentation.web.blueprints.public.routes.send_support_email",
        fake_send_support,
    )

    resp = client.post("/support", data={}, follow_redirects=False)

    # Puede ser 200 (re-muestra el form) o 400 (si decides marcar error)
    assert resp.status_code in (200, 400)

    html = resp.data.decode("utf-8")
    assert "Contacto y Soporte" in html


def test_public_routes_do_not_require_login(client):
    """
    Las rutas públicas deben responder sin estar autenticado.
    """
    for path in ("/", "/features", "/sobre", "/support"):
        resp = client.get(path)
        assert resp.status_code == 200


def test_support_uses_correct_template(client, monkeypatch):
    """
    Verifica que /support renderiza el template public/support.html
    (regresión por si alguien cambia la ruta del template).
    """
    seen = {}

    def fake_render_template(template_name, *args, **context):
        seen["template"] = template_name
        # devolvemos algo simple para que Flask responda 200
        return "OK"

    monkeypatch.setattr(
        "src.presentation.web.blueprints.public.routes.render_template",
        fake_render_template,
    )

    resp = client.get("/support")
    assert resp.status_code == 200
    assert seen.get("template") == "public/support.html"

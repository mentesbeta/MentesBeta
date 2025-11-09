from flask import Blueprint, render_template, request, current_app
from src.infrastructure.notifications.support_mail import send_support_email 

public_bp = Blueprint("public", __name__)

@public_bp.route("/")
def index():
    return render_template("public/index.html", title="Incidex")

@public_bp.route("/features")
def features():
    return render_template("public/features.html", title="Características")

@public_bp.route("/support", methods=["GET", "POST"])
def support():
    if request.method == "POST":
        nombre  = (request.form.get("nombre")  or "").strip()
        correo  = (request.form.get("correo")  or "").strip()
        asunto  = (request.form.get("asunto")  or "").strip()
        mensaje = (request.form.get("mensaje") or "").strip()

        errors = []

        if not nombre:
            errors.append("El nombre es obligatorio.")
        if not correo:
            errors.append("El correo es obligatorio.")
        if not asunto:
            errors.append("El asunto es obligatorio.")
        if not mensaje:
            errors.append("El mensaje es obligatorio.")

        sent_ok = False
        if not errors:
            try:
                send_support_email(nombre, correo, asunto, mensaje)
                sent_ok = True
                # opcional: limpiar form si quieres
                form_data = {"nombre": "", "correo": "", "asunto": "", "mensaje": ""}
            except Exception as e:
                current_app.logger.exception("Error enviando correo de soporte")
                errors.append("No se pudo enviar el mensaje. Inténtalo nuevamente más tarde.")
                form_data = {
                    "nombre": nombre,
                    "correo": correo,
                    "asunto": asunto,
                    "mensaje": mensaje,
                }
        else:
            form_data = {
                "nombre": nombre,
                "correo": correo,
                "asunto": asunto,
                "mensaje": mensaje,
            }

        return render_template(
            "public/support.html",
            title="Soporte",
            sent_ok=sent_ok,
            errors=errors,
            form_data=form_data,
        )

    # GET simple
    return render_template("public/support.html", title="Soporte")

@public_bp.route("/sobre")
def about():
    return render_template("public/about.html", title="Sobre Incidex")


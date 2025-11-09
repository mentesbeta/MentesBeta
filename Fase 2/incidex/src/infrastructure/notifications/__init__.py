import smtplib
from email.message import EmailMessage
from flask import current_app


def send_support_email(nombre: str, correo: str, asunto: str, mensaje: str) -> None:
    """
    Envía un correo de soporte al administrador definido en la configuración.

    Config esperada en app.config:
      SUPPORT_EMAIL_TO   -> correo destino (admin escritorio)
      SUPPORT_EMAIL_FROM -> correo remitente (opcional, por defecto igual al TO)
      MAIL_SERVER        -> host SMTP
      MAIL_PORT          -> puerto (ej: 587)
      MAIL_USERNAME      -> usuario SMTP (opcional)
      MAIL_PASSWORD      -> password SMTP (opcional)
      MAIL_USE_TLS       -> True/False (opcional)
      MAIL_USE_SSL       -> True/False (opcional)
    """

    to_addr = current_app.config.get("SUPPORT_EMAIL_TO", "soporte@incidex.cl")
    from_addr = current_app.config.get("SUPPORT_EMAIL_FROM", to_addr)

    subject = f"[Incidex · Soporte] {asunto}".strip()

    body = f"""Se ha recibido un nuevo mensaje de soporte desde la web pública.

Nombre: {nombre}
Correo: {correo}

Mensaje:
{mensaje}
"""

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_addr
    msg.set_content(body)

    host = current_app.config.get("MAIL_SERVER", "localhost")
    port = int(current_app.config.get("MAIL_PORT", 25))
    username = current_app.config.get("MAIL_USERNAME")
    password = current_app.config.get("MAIL_PASSWORD")
    use_tls = bool(current_app.config.get("MAIL_USE_TLS", False))
    use_ssl = bool(current_app.config.get("MAIL_USE_SSL", False))

    if use_ssl:
        with smtplib.SMTP_SSL(host, port) as smtp:
            if username and password:
                smtp.login(username, password)
            smtp.send_message(msg)
    else:
        with smtplib.SMTP(host, port) as smtp:
            if use_tls:
                smtp.starttls()
            if username and password:
                smtp.login(username, password)
            smtp.send_message(msg)

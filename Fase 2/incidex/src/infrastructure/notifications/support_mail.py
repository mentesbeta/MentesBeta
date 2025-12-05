import smtplib
from email.message import EmailMessage
from flask import current_app


def send_support_email(nombre: str, correo: str, asunto: str, mensaje: str) -> None:
    to_addr = current_app.config.get("SUPPORT_EMAIL_TO", "soporte@incidex.cl")
    from_addr = current_app.config.get("SUPPORT_EMAIL_FROM", to_addr)

    subject = f"[Incidex Soporte] {asunto}".strip()

    # --- versión mejorada del mensaje ---
    text_body = f"""\
Se ha recibido un nuevo mensaje de soporte desde la web pública.

Nombre: {nombre}
Correo: {correo}

Mensaje:
{mensaje}
"""

    # Evita el error del backslash dentro de f-string
    safe_message = mensaje.replace("\n", "<br>")

    html_body = f"""\
<html>
  <body style="font-family:Arial, sans-serif; background-color:#f7f9fc; padding:20px;">
    <table style="max-width:600px; margin:auto; background:#ffffff; border-radius:10px; padding:20px; border:1px solid #e2e8f0;">
      <tr>
        <td style="text-align:center;">
          <h2 style="color:#1e63d1;">Nuevo mensaje de soporte</h2>
        </td>
      </tr>
      <tr>
        <td style="padding:10px 0; color:#111;">
          <p><strong>Nombre:</strong> {nombre}</p>
          <p><strong>Correo:</strong> <a href="mailto:{correo}">{correo}</a></p>
          <p><strong>Asunto:</strong> {asunto}</p>
          <div style="margin-top:15px; padding:12px; background:#f1f5f9; border-radius:8px;">
            <strong>Mensaje:</strong><br>
            {safe_message}
          </div>
        </td>
      </tr>
      <tr>
        <td style="text-align:center; padding-top:20px; font-size:13px; color:#64748b;">
          Este correo fue generado automáticamente por <strong>Incidex</strong> — Plataforma de gestión de incidencias.
        </td>
      </tr>
    </table>
  </body>
</html>
"""

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_addr
    msg.set_content(text_body)
    msg.add_alternative(html_body, subtype="html")

    host = current_app.config.get("MAIL_SERVER", "localhost")
    port = int(current_app.config.get("MAIL_PORT", 25))
    username = current_app.config.get("MAIL_USERNAME")
    password = current_app.config.get("MAIL_PASSWORD")
    use_tls = bool(current_app.config.get("MAIL_USE_TLS", False))
    use_ssl = bool(current_app.config.get("MAIL_USE_SSL", False))

    # DEBUG: log visible
    current_app.logger.info(
        f"Enviando soporte via SMTP host={host} port={port} tls={use_tls} ssl={use_ssl} user={username}"
    )

    # ── Bloque protegido: si algo falla, se registra pero NO rompe la app ──
    try:
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
    except Exception as e:
        current_app.logger.warning(f"[Support Email Error] {e}")


def send_notification_email(to_email: str, title: str, message: str) -> None:
    """
    Envía un correo de notificación a un usuario (cuando se crea una
    notificación en la campanita).
    NO toca la lógica de soporte, reutiliza la misma config SMTP.
    Si falla, NO rompe el flujo (solo loguea el error).
    """
    if not to_email:
        return

    subject = f"[Incidex] {title}".strip()

    text_body = f"""\
{message}

---

Este es un mensaje automático de Incidex.
Por favor ingresa a la plataforma para revisar los detalles del ticket.
"""

    safe_message = message.replace("\n", "<br>")

    html_body = f"""\
<html>
  <body style="font-family:Arial, sans-serif; background-color:#f7f9fc; padding:20px;">
    <table style="max-width:600px; margin:auto; background:#ffffff; border-radius:10px; padding:20px; border:1px solid #e2e8f0;">
      <tr>
        <td style="text-align:center;">
          <h2 style="color:#1e63d1;">Notificación de Incidex</h2>
        </td>
      </tr>
      <tr>
        <td style="padding:10px 0; color:#111;">
          <p>{safe_message}</p>
          <p style="margin-top:16px; font-size:13px; color:#64748b;">
            Ingresa a <strong>Incidex</strong> para ver el detalle del ticket.
          </p>
        </td>
      </tr>
      <tr>
        <td style="text-align:center; padding-top:20px; font-size:12px; color:#94a3b8;">
          Este correo fue generado automáticamente por <strong>Incidex</strong>.
          Por favor no respondas a este mensaje.
        </td>
      </tr>
    </table>
  </body>
</html>
"""

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = current_app.config.get("SUPPORT_EMAIL_FROM", "no-reply@incidex.cl")
    msg["To"] = to_email
    msg.set_content(text_body)
    msg.add_alternative(html_body, subtype="html")

    host = current_app.config.get("MAIL_SERVER", "localhost")
    port = int(current_app.config.get("MAIL_PORT", 25))
    username = current_app.config.get("MAIL_USERNAME")
    password = current_app.config.get("MAIL_PASSWORD")
    use_tls = bool(current_app.config.get("MAIL_USE_TLS", False))
    use_ssl = bool(current_app.config.get("MAIL_USE_SSL", False))

    current_app.logger.info(
        f"Enviando notificación via SMTP host={host} port={port} tls={use_tls} ssl={use_ssl} user={username}"
    )

    # ── Bloque protegido: si el SMTP o el correo fallan, solo se loguea ──
    try:
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
    except Exception as e:
        current_app.logger.warning(f"[Notification Email Error] {e}")

import json
import logging
import smtplib
from email.message import EmailMessage
from urllib import request

from flask import current_app

logger = logging.getLogger(__name__)


def send_email(subject: str, body: str, recipients: list[str], html: str | None = None) -> dict:
    recipients = [r.strip().lower() for r in recipients if r]
    if not recipients:
        return {"sent": False, "reason": "no_recipients"}

    if current_app.config.get("MAIL_SUPPRESS_SEND", False):
        current_app.extensions.setdefault("sent_emails", []).append(
            {"subject": subject, "body": body, "html": html, "recipients": recipients}
        )
        return {"sent": True, "suppressed": True, "recipients": recipients}

    host = current_app.config.get("SMTP_HOST")
    if not host:
        logger.warning("SMTP_HOST not configured. Email not sent.")
        return {"sent": False, "reason": "smtp_not_configured", "recipients": recipients}

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = current_app.config.get("MAIL_FROM", current_app.config.get("ADMIN_EMAIL"))
    msg["To"] = ", ".join(recipients)
    msg.set_content(body)
    if html:
        msg.add_alternative(html, subtype="html")

    port = int(current_app.config.get("SMTP_PORT", 25))
    use_tls = bool(current_app.config.get("SMTP_USE_TLS", False))
    username = current_app.config.get("SMTP_USERNAME")
    password = current_app.config.get("SMTP_PASSWORD")

    try:
        with smtplib.SMTP(host, port, timeout=10) as smtp:
            if use_tls:
                smtp.starttls()
            if username and password:
                smtp.login(username, password)
            smtp.send_message(msg)
        return {"sent": True, "recipients": recipients}
    except Exception as exc:
        logger.exception("Failed to send email")
        return {"sent": False, "reason": str(exc), "recipients": recipients}


def send_chat_webhook(message: str) -> dict:
    url = current_app.config.get("CHAT_WEBHOOK_URL")
    if not url:
        return {"sent": False, "reason": "webhook_not_configured"}

    payload = json.dumps({"text": message}).encode("utf-8")
    req = request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with request.urlopen(req, timeout=10) as resp:
            return {"sent": 200 <= resp.status < 300, "status": resp.status}
    except Exception as exc:
        logger.exception("Failed to send chat webhook")
        return {"sent": False, "reason": str(exc)}

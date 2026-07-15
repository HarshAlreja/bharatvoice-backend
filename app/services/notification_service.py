"""SMTP email sending -- OTP codes, admin alerts, invoice notifications."""
import logging
import smtplib
from email.mime.text import MIMEText
from flask import current_app

logger = logging.getLogger(__name__)

SMTP_TIMEOUT_SECONDS = 10  # fail fast instead of hanging the whole Flask process


def send_email(to_email: str, subject: str, body: str) -> bool:
    """
    Returns True/False instead of raising -- a broken SMTP config should
    never crash or hang a request (like signup) that triggers an email.
    Without an explicit timeout, smtplib can block forever on a bad
    host/port/firewall, which freezes Flask's single-threaded dev server
    for every other request too.
    """
    try:
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = current_app.config["SMTP_USER"]
        msg["To"] = to_email

        with smtplib.SMTP(
            current_app.config["SMTP_HOST"],
            current_app.config["SMTP_PORT"],
            timeout=SMTP_TIMEOUT_SECONDS,
        ) as server:
            server.starttls()
            server.login(current_app.config["SMTP_USER"], current_app.config["SMTP_PASSWORD"])
            server.send_message(msg)
        return True
    except Exception as exc:
        logger.error("Failed to send email to %s: %s", to_email, exc)
        return False


def send_otp_email(to_email: str, code: str) -> bool:
    sent = send_email(
        to_email, "Your BharatVoice verification code",
        f"Your code is: {code}\nExpires in 10 minutes."
    )
    if not sent:
        # Dev/testing fallback -- so signup isn't a dead end just because
        # SMTP isn't configured correctly yet. Remove this print before
        # going to production.
        logger.warning("SMTP failed -- OTP for %s is: %s (dev fallback, check console)", to_email, code)
    return sent
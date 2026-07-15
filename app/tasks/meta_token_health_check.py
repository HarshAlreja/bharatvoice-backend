"""
Cron job: periodically ping each connected WABA to confirm its access token is
still valid. Meta occasionally invalidates tokens (owner revokes permission,
password change, etc). Flags dead connections so the client sees a reconnect
prompt instead of silently failing on the next customer message. Run every few
hours.
"""
import requests
from app.extensions import db
from app.models.whatsapp_number import WhatsAppNumber
from app.utils.security import decrypt_token
from flask import current_app

META_GRAPH_BASE = "https://graph.facebook.com"


def run():
    version = current_app.config["META_API_VERSION"]
    numbers = WhatsAppNumber.query.filter_by(status="connected").all()

    for number in numbers:
        try:
            token = decrypt_token(number.access_token_encrypted)
            resp = requests.get(
                f"{META_GRAPH_BASE}/{version}/{number.phone_number_id}",
                params={"access_token": token},
                timeout=10,
            )
            if resp.status_code != 200:
                number.status = "error"
        except Exception:
            number.status = "error"

    db.session.commit()

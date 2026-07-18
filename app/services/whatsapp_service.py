"""
Sends messages via each business's OWN token + phone_number_id. Every call here
looks up the correct WhatsAppNumber row first -- there is no shared credential.
"""
import requests
from flask import current_app
from app.models.whatsapp_number import WhatsAppNumber
from app.utils.security import decrypt_token

META_GRAPH_BASE = "https://graph.facebook.com"


def send_text_message(business_id: int, to_phone: str, body: str) -> dict:
    # Always resolve the sending number/token from THIS business's own
    # connected WhatsAppNumber row. No env-var shortcuts, no shared credential --
    # this is what makes replies multi-tenant safe.
    number = WhatsAppNumber.query.filter_by(business_id=business_id, status="connected").first()
    if not number:
        raise ValueError(f"No connected WhatsApp number for business_id={business_id}")

    access_token = decrypt_token(number.access_token_encrypted)
    phone_number_id = number.phone_number_id
    version = current_app.config.get("META_API_VERSION", "v22.0")

    resp = requests.post(
        f"{META_GRAPH_BASE}/{version}/{phone_number_id}/messages",
        headers={"Authorization": f"Bearer {access_token}"},
        json={
            "messaging_product": "whatsapp",
            "to": to_phone,
            "type": "text",
            "text": {"body": body},
        },
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


def resolve_business_by_phone_number_id(phone_number_id: str):
    """Used by the webhook to figure out which tenant an incoming message belongs to.

    Pure DB lookup -- the phone_number_id Meta sends in the webhook payload is the
    single source of truth for which business a message belongs to. No hardcoded
    fallback business_id here; if we can't find a match, the caller should treat
    this as "unknown business" and not silently attribute it to anyone.
    """
    number = WhatsAppNumber.query.filter_by(phone_number_id=phone_number_id).first()
    return number.business_id if number else None
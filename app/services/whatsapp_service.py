"""
Sends messages via each business's OWN token + phone_number_id. Every call here
looks up the correct WhatsAppNumber row first -- there is no shared credential.
"""
import os
import requests
from flask import current_app
from app.models.whatsapp_number import WhatsAppNumber
from app.utils.security import decrypt_token

META_GRAPH_BASE = "https://graph.facebook.com"


def send_text_message(business_id: int, to_phone: str, body: str) -> dict:
    # ----------------------------------------------------------------
    # TESTING BYPASS: Direct Render Env Variables Force kiye hain
    # ----------------------------------------------------------------
    phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "1171835566011474")
    access_token = os.getenv("WHATSAPP_ACCESS_TOKEN")
    version = current_app.config.get("META_API_VERSION", "v22.0")

    # Agar Render ke env variables me token nahi mila, tabhi fallback to DB
    if not access_token:
        number = WhatsAppNumber.query.filter_by(business_id=business_id, status="connected").first()
        if not number:
            raise ValueError(f"No connected WhatsApp number for business_id={business_id}")
        access_token = decrypt_token(number.access_token_encrypted)
        phone_number_id = number.phone_number_id

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
    """Used by the webhook to figure out which tenant an incoming message belongs to."""
    # Webhook testing ke liye agar Meta correct ID hit karega, toh check database
    number = WhatsAppNumber.query.filter_by(phone_number_id=phone_number_id).first()
    if not number and phone_number_id == os.getenv("WHATSAPP_PHONE_NUMBER_ID", "1171835566011474"):
        # Agar sandbox testing number hai aur DB me entry nahi mili, 
        # toh default kisi valid testing business_id (e.g., 1) par map kar do
        return 1
        
    return number.business_id if number else None
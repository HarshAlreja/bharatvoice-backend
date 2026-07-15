"""
Handles the Embedded Signup code-exchange flow. This runs ONCE PER CLIENT, in
seconds, fully automated -- this is NOT the manual System User setup you do once
for your own Meta Developer App (that lives outside this service, done by hand
in Meta Business Suite, one time only, for the platform itself).

Flow per client:
1. Frontend loads Meta's JS SDK, launches Embedded Signup popup (client does
   Facebook login, creates/selects Business Portfolio, creates/selects WABA,
   adds + verifies their phone number -- all inside Meta's own UI).
2. Popup closes, frontend receives a short-lived `code`.
3. Frontend POSTs that code to /api/whatsapp/callback (see client/whatsapp.py).
4. This service exchanges the code for a long-lived Business Integration System
   User access token (scoped to that one client), fetches their WABA ID / phone
   number ID, and subscribes the webhook -- all server-side, all automatic.
"""
import requests
from flask import current_app
from app.utils.security import encrypt_token


META_GRAPH_BASE = "https://graph.facebook.com"


def exchange_code_for_token(code: str) -> dict:
    """Step 1: exchange the Embedded Signup `code` for a long-lived access token."""
    version = current_app.config["META_API_VERSION"]
    resp = requests.get(
        f"{META_GRAPH_BASE}/{version}/oauth/access_token",
        params={
            "client_id": current_app.config["META_APP_ID"],
            "client_secret": current_app.config["META_APP_SECRET"],
            "code": code,
        },
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()  # { access_token, token_type, expires_in }


def fetch_waba_assets(access_token: str) -> dict:
    """Step 2: use the token to discover which WABA / phone number this client just connected."""
    version = current_app.config["META_API_VERSION"]
    resp = requests.get(
        f"{META_GRAPH_BASE}/{version}/me/whatsapp_business_accounts",
        params={"access_token": access_token},
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json().get("data", [])
    if not data:
        raise ValueError("No WABA found for this access token")
    waba = data[0]

    numbers_resp = requests.get(
        f"{META_GRAPH_BASE}/{version}/{waba['id']}/phone_numbers",
        params={"access_token": access_token},
        timeout=15,
    )
    numbers_resp.raise_for_status()
    numbers = numbers_resp.json().get("data", [])
    if not numbers:
        raise ValueError("No phone number found on this WABA yet")
    number = numbers[0]

    return {
        "waba_id": waba["id"],
        "phone_number_id": number["id"],
        "display_number": number.get("display_phone_number"),
    }


def subscribe_webhook(waba_id: str, access_token: str) -> None:
    """Step 3: subscribe BharatVoice's app to this client's WABA events."""
    version = current_app.config["META_API_VERSION"]
    resp = requests.post(
        f"{META_GRAPH_BASE}/{version}/{waba_id}/subscribed_apps",
        params={"access_token": access_token},
        timeout=15,
    )
    resp.raise_for_status()


def complete_client_onboarding(business_id: int, code: str):
    """
    Full pipeline for one client. Called by
    POST /api/whatsapp/callback (see routes/client/whatsapp.py).
    Returns the WhatsAppNumber row, fully populated and connected.
    """
    from app.extensions import db
    from app.models.whatsapp_number import WhatsAppNumber
    from datetime import datetime, timedelta

    token_data = exchange_code_for_token(code)
    access_token = token_data["access_token"]
    expires_in = token_data.get("expires_in")  # None for non-expiring business tokens

    assets = fetch_waba_assets(access_token)
    subscribe_webhook(assets["waba_id"], access_token)

    number = WhatsAppNumber.query.filter_by(business_id=business_id).first()
    if not number:
        number = WhatsAppNumber(business_id=business_id)
        db.session.add(number)

    number.waba_id = assets["waba_id"]
    number.phone_number_id = assets["phone_number_id"]
    number.display_number = assets["display_number"]
    number.access_token_encrypted = encrypt_token(access_token)
    number.token_expires_at = (
        datetime.utcnow() + timedelta(seconds=expires_in) if expires_in else None
    )
    number.status = "connected"
    number.connected_at = datetime.utcnow()

    db.session.commit()
    return number

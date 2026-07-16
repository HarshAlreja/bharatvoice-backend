"""
Handles the Embedded Signup code-exchange flow. This runs ONCE PER CLIENT, in
seconds, fully automated -- this is NOT the manual System User setup you do once
for your own Meta Developer App (that lives outside this service, done by hand
in Meta Business Suite, one time only, for the platform itself).

Flow per client:
1. Frontend loads Meta's JS SDK, launches Embedded Signup popup (client does
   Facebook login, creates/selects Business Portfolio, creates/selects WABA,
   adds + verifies their phone number -- all inside Meta's own UI).
2. Popup closes, frontend receives a short-lived `code` (from FB.login's
   callback) AND a `waba_id` + `phone_number_id` (from Meta's separate
   postMessage "WA_EMBEDDED_SIGNUP" event -- these do NOT come from the same
   place as `code`, and the frontend must listen for both).
3. Frontend POSTs code + waba_id + phone_number_id to /api/whatsapp/callback.
4. This service exchanges the code for a long-lived Business Integration
   System User access token, then uses the waba_id/phone_number_id the
   FRONTEND already gave it (does NOT try to "discover" them via a Graph API
   call like /me/whatsapp_business_accounts -- that endpoint is unreliable
   for this purpose and returns 400 Bad Request in practice), subscribes the
   webhook, and stores everything.
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


def fetch_display_number(phone_number_id: str, access_token: str) -> str:
    """Fetch the human-readable display number for a given phone_number_id.
    This is a targeted lookup (we already know the ID), not a discovery call --
    much more reliable than trying to enumerate WABAs/numbers from scratch."""
    version = current_app.config["META_API_VERSION"]
    resp = requests.get(
        f"{META_GRAPH_BASE}/{version}/{phone_number_id}",
        params={"access_token": access_token, "fields": "display_phone_number"},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json().get("display_phone_number", "")


def subscribe_webhook(waba_id: str, access_token: str) -> None:
    """Subscribe BharatVoice's app to this client's WABA events."""
    version = current_app.config["META_API_VERSION"]
    resp = requests.post(
        f"{META_GRAPH_BASE}/{version}/{waba_id}/subscribed_apps",
        params={"access_token": access_token},
        timeout=15,
    )
    resp.raise_for_status()


def complete_client_onboarding(business_id: int, code: str, waba_id: str, phone_number_id: str):
    """
    Full pipeline for one client. Called by
    POST /api/whatsapp/callback (see routes/client/whatsapp.py).

    waba_id and phone_number_id come from the FRONTEND (captured via Meta's
    postMessage event during the popup flow) -- not re-derived here. This is
    the fix for the "400 Bad Request on /me/whatsapp_business_accounts" bug.
    """
    from app.extensions import db
    from app.models.whatsapp_number import WhatsAppNumber
    from datetime import datetime, timedelta

    token_data = exchange_code_for_token(code)
    access_token = token_data["access_token"]
    expires_in = token_data.get("expires_in")  # None for non-expiring business tokens

    subscribe_webhook(waba_id, access_token)
    display_number = fetch_display_number(phone_number_id, access_token)

    number = WhatsAppNumber.query.filter_by(business_id=business_id).first()
    if not number:
        number = WhatsAppNumber(business_id=business_id)
        db.session.add(number)

    number.waba_id = waba_id
    number.phone_number_id = phone_number_id
    number.display_number = display_number
    number.access_token_encrypted = encrypt_token(access_token)
    number.token_expires_at = (
        datetime.utcnow() + timedelta(seconds=expires_in) if expires_in else None
    )
    number.status = "connected"
    number.connected_at = datetime.utcnow()

    db.session.commit()
    return number
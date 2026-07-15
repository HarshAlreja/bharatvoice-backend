"""
Client-side WhatsApp connection routes. The heavy lifting (code exchange, WABA
lookup, webhook subscribe) lives in meta_oauth_service -- this file just wires
HTTP in/out and enforces tenant scoping.
"""
from flask import Blueprint, request, g
from app.models.whatsapp_number import WhatsAppNumber
from app.middleware.tenant_guard import tenant_required
from app.services.meta_oauth_service import complete_client_onboarding
from app.services.whatsapp_service import send_text_message
from app.utils.responses import success, error

client_whatsapp_bp = Blueprint("client_whatsapp", __name__)


@client_whatsapp_bp.route("/whatsapp/status", methods=["GET"])
@tenant_required
def status():
    number = WhatsAppNumber.query.filter_by(business_id=g.business_id).first()
    if not number:
        return success({"status": "not_connected"})

    return success({
        "status": number.status,
        "display_number": number.display_number,
        "phone_number_id": number.phone_number_id,
        "waba_id": number.waba_id,
        "verification_status": number.verification_status,
        "daily_message_limit": number.daily_message_limit,
        "connected_at": number.connected_at.isoformat() if number.connected_at else None,
    })


@client_whatsapp_bp.route("/whatsapp/callback", methods=["POST"])
@tenant_required
def callback():
    """Frontend calls this right after the Embedded Signup popup closes, with the
    `code` Meta handed back. Everything after this is automatic."""
    body = request.get_json(silent=True) or {}
    code = body.get("code")
    if not code:
        return error("Missing code from Embedded Signup")

    try:
        number = complete_client_onboarding(g.business_id, code)
    except Exception as exc:
        return error(f"WhatsApp connection failed: {exc}", 502)

    return success({
        "status": number.status,
        "display_number": number.display_number,
    }, "WhatsApp connected")


@client_whatsapp_bp.route("/whatsapp/disconnect", methods=["POST"])
@tenant_required
def disconnect():
    from app.extensions import db

    number = WhatsAppNumber.query.filter_by(business_id=g.business_id).first()
    if not number:
        return error("No connection found", 404)

    number.status = "disconnected"
    db.session.commit()
    return success(message="Disconnected")


@client_whatsapp_bp.route("/whatsapp/test-message", methods=["POST"])
@tenant_required
def test_message():
    body = request.get_json(silent=True) or {}
    phone = body.get("phone_number")
    message = body.get("message", "Test message from BharatVoice")

    if not phone:
        return error("phone_number required")

    try:
        send_text_message(g.business_id, phone, message)
    except Exception as exc:
        return error(f"Send failed: {exc}", 502)

    return success(message="Test message sent")
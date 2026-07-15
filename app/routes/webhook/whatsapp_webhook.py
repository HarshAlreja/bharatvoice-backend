"""
ONE public endpoint. Every business's incoming WhatsApp messages hit this same
URL -- Meta doesn't know or care about your multi-tenant setup. Routing to the
correct business happens entirely by looking up phone_number_id.
"""
from flask import Blueprint, request, current_app
from app.extensions import db
from app.models.conversation import Conversation
from app.models.message import Message
from app.services.whatsapp_service import resolve_business_by_phone_number_id, send_text_message
from app.services.rag_service import retrieve_context
from app.services.groq_service import generate_reply

webhook_bp = Blueprint("webhook", __name__)


@webhook_bp.route("/whatsapp", methods=["GET"])
def verify_webhook():
    """Meta's one-time verification handshake when you register the webhook URL."""
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == current_app.config["META_WEBHOOK_VERIFY_TOKEN"]:
        return challenge, 200
    return "Verification failed", 403


@webhook_bp.route("/whatsapp", methods=["POST"])
def receive_message():
    payload = request.get_json(silent=True) or {}

    try:
        entry = payload["entry"][0]
        change = entry["changes"][0]["value"]
        phone_number_id = change["metadata"]["phone_number_id"]
        incoming = change.get("messages", [None])[0]
    except (KeyError, IndexError, TypeError):
        return "ignored", 200  # status update / non-message event, not an error

    if not incoming:
        return "ignored", 200

    business_id = resolve_business_by_phone_number_id(phone_number_id)
    if not business_id:
        current_app.logger.warning(f"No business found for phone_number_id={phone_number_id}")
        return "unknown number", 200

    customer_phone = incoming["from"]
    text_body = incoming.get("text", {}).get("body", "")

    conversation = (
        Conversation.query.filter_by(business_id=business_id, customer_phone=customer_phone, status="active")
        .first()
    )
    if not conversation:
        conversation = Conversation(business_id=business_id, customer_phone=customer_phone)
        db.session.add(conversation)
        db.session.flush()

    db.session.add(Message(conversation_id=conversation.id, sender="customer", content=text_body))
    db.session.commit()

    context_chunks = retrieve_context(business_id, text_body)
    reply_text = generate_reply(business_id, conversation.id, context_chunks, text_body)

    db.session.add(Message(conversation_id=conversation.id, sender="bot", content=reply_text))
    db.session.commit()

    send_text_message(business_id, customer_phone, reply_text)

    return "ok", 200

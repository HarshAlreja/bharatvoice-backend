"""Cross-tenant conversation oversight (support/abuse investigation)."""
from flask import Blueprint, request
from app.extensions import db
from app.models.conversation import Conversation
from app.models.message import Message
from app.middleware.admin_guard import admin_required
from app.utils.responses import success

admin_conversations_bp = Blueprint("admin_conversations", __name__)


@admin_conversations_bp.route("/conversations", methods=["GET"])
@admin_required
def list_conversations():
    business_id = request.args.get("business_id")
    query = Conversation.query
    if business_id:
        query = query.filter_by(business_id=business_id)

    convs = query.order_by(Conversation.started_at.desc()).limit(200).all()
    return success({"conversations": [
        {"id": c.id, "business_id": c.business_id, "customer_phone": c.customer_phone, "status": c.status}
        for c in convs
    ]})


@admin_conversations_bp.route("/conversations/<int:conv_id>", methods=["DELETE"])
@admin_required
def delete_conversation(conv_id):
    Message.query.filter_by(conversation_id=conv_id).delete()
    Conversation.query.filter_by(id=conv_id).delete()
    db.session.commit()
    return success(message="Conversation purged")

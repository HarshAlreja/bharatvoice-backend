"""Tenant dashboard overview metrics."""
from datetime import datetime, timedelta
from flask import Blueprint, g
from sqlalchemy import func
from app.extensions import db
from app.models.conversation import Conversation
from app.models.document import Document
from app.models.whatsapp_number import WhatsAppNumber
from app.models.token_usage_log import TokenUsageLog
from app.middleware.tenant_guard import tenant_required
from app.utils.responses import success

client_dashboard_bp = Blueprint("client_dashboard", __name__)


@client_dashboard_bp.route("/dashboard/overview", methods=["GET"])
@tenant_required
def overview():
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    bid = g.business_id

    conversations_30_days = db.session.query(func.count(Conversation.id)).filter(
        Conversation.business_id == bid, Conversation.started_at >= thirty_days_ago
    ).scalar() or 0

    documents_count = db.session.query(func.count(Document.id)).filter(
        Document.business_id == bid
    ).scalar() or 0

    whatsapp = WhatsAppNumber.query.filter_by(business_id=bid, status="connected").first()

    tokens_used = db.session.query(func.sum(TokenUsageLog.tokens_used)).filter(
        TokenUsageLog.business_id == bid, TokenUsageLog.created_at >= thirty_days_ago
    ).scalar() or 0

    return success({
        "conversations_30_days": conversations_30_days,
        "documents_count": documents_count,
        "whatsapp_connected": whatsapp is not None,
        "tokens_used": tokens_used,
    })

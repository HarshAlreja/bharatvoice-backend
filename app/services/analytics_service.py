"""Aggregation queries for admin dashboard / analytics / revenue pages."""
from datetime import datetime, timedelta
from sqlalchemy import func
from app.extensions import db
from app.models.business import Business
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.document import Document
from app.models.whatsapp_number import WhatsAppNumber
from app.models.token_usage_log import TokenUsageLog


def compute_avg_response_time_seconds(conversation_ids):
    """
    Shared helper: pairs each customer message with the bot reply that
    follows it in the same conversation, returns the average delay in
    seconds (or None if there's no data yet).

    This used to be duplicated separately inside client/conversations.py
    and client/analytics.py -- it now lives in exactly one place, and both
    of those routes should import and call this instead of recomputing it
    inline. (If you haven't updated those call sites yet, they'll still
    work with their own inline copy -- just know there are now two versions
    of the same logic until that cleanup happens.)
    """
    if not conversation_ids:
        return None

    messages = (
        Message.query.filter(Message.conversation_id.in_(conversation_ids))
        .order_by(Message.conversation_id, Message.created_at)
        .all()
    )

    pending = {}
    deltas_seconds = []
    for m in messages:
        if m.sender == "customer":
            pending[m.conversation_id] = m
        elif m.sender == "bot" and m.conversation_id in pending:
            customer_msg = pending.pop(m.conversation_id)
            delta = (m.created_at - customer_msg.created_at).total_seconds()
            if delta >= 0:
                deltas_seconds.append(delta)

    if not deltas_seconds:
        return None
    return round(sum(deltas_seconds) / len(deltas_seconds), 1)


def platform_dashboard_summary():
    """
    Platform-wide summary across ALL businesses -- used by admin/dashboard.py
    to populate admin-dashboard.html's telemetry cards. No business_id filter
    -- this is intentionally cross-tenant.

    Shape MUST match what admin-dashboard.js's updateTelemetryUI() reads:
    data.users.total, data.businesses.total, data.whatsapp.active,
    data.documents.total, data.conversations.recent_30_days,
    data.ai_usage.total_tokens_used, data.ai_usage.recent_30_days_tokens
    """
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)

    return {
        "users": {"total": db.session.query(func.count(Business.id)).scalar() or 0},
        "businesses": {"total": db.session.query(func.count(Business.id)).scalar() or 0},
        "whatsapp": {
            "active": db.session.query(func.count(WhatsAppNumber.id))
            .filter(WhatsAppNumber.status == "connected").scalar() or 0
        },
        "documents": {"total": db.session.query(func.count(Document.id)).scalar() or 0},
        "conversations": {
            "recent_30_days": db.session.query(func.count(Conversation.id))
            .filter(Conversation.started_at >= thirty_days_ago).scalar() or 0
        },
        "ai_usage": {
            "total_tokens_used": db.session.query(func.sum(TokenUsageLog.tokens_used)).scalar() or 0,
            "recent_30_days_tokens": db.session.query(func.sum(TokenUsageLog.tokens_used))
            .filter(TokenUsageLog.created_at >= thirty_days_ago).scalar() or 0,
        },
    }
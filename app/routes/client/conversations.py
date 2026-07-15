"""
List / search / export conversations. Read-only, populated by the webhook.

The frontend displays one row per "exchange" (customer message + the bot's
reply that followed it) -- not one row per conversation thread. This file
builds those exchange rows by pairing consecutive customer/bot messages
within each conversation, since that's the actual data the UI needs and
the raw Conversation model alone can't provide it.
"""
from datetime import datetime, timedelta
from flask import Blueprint, request, g
from app.models.conversation import Conversation
from app.models.message import Message
from app.middleware.tenant_guard import tenant_required
from app.utils.csv_export import stream_csv
from app.utils.responses import success

client_conversations_bp = Blueprint("client_conversations", __name__)


def _date_cutoff(date_filter: str):
    now = datetime.utcnow()
    if date_filter == "today":
        return now.replace(hour=0, minute=0, second=0, microsecond=0)
    if date_filter == "week":
        return now - timedelta(days=7)
    if date_filter == "month":
        return now - timedelta(days=30)
    return None


def _build_exchange_rows(business_id: int, date_filter: str = "all"):
    """Pair each customer message with the bot reply that immediately follows
    it in the same conversation. Returns rows sorted newest-first."""
    conversations = Conversation.query.filter_by(business_id=business_id).all()
    conv_ids = [c.id for c in conversations]
    if not conv_ids:
        return []

    phone_by_conv = {c.id: c.customer_phone for c in conversations}

    messages = (
        Message.query.filter(Message.conversation_id.in_(conv_ids))
        .order_by(Message.conversation_id, Message.created_at)
        .all()
    )

    cutoff = _date_cutoff(date_filter)
    rows = []
    pending_customer_msg = {}  # conversation_id -> last unanswered customer Message

    for m in messages:
        if m.sender == "customer":
            pending_customer_msg[m.conversation_id] = m
        elif m.sender == "bot" and m.conversation_id in pending_customer_msg:
            customer_msg = pending_customer_msg.pop(m.conversation_id)

            if cutoff and customer_msg.created_at < cutoff:
                continue

            response_time_ms = int((m.created_at - customer_msg.created_at).total_seconds() * 1000)
            rows.append({
                "timestamp": customer_msg.created_at.isoformat(),
                "customer_phone": phone_by_conv.get(m.conversation_id, ""),
                "message": customer_msg.content,
                "ai_response": m.content,
                "message_type": "text",  # voice notes aren't wired into the webhook yet
                "response_time_ms": max(response_time_ms, 0),
            })

    rows.sort(key=lambda r: r["timestamp"], reverse=True)
    return rows


@client_conversations_bp.route("/conversations/summary", methods=["GET"])
@tenant_required
def conversations_summary():
    rows = _build_exchange_rows(g.business_id, date_filter="all")

    today_cutoff = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_count = sum(1 for r in rows if r["timestamp"] >= today_cutoff.isoformat())

    unique_customers = len({r["customer_phone"] for r in rows})
    avg_response = (
        sum(r["response_time_ms"] for r in rows) / len(rows) if rows else 0
    )

    return success({
        "total_conversations": len(rows),
        "unique_customers": unique_customers,
        "avg_response_time_ms": round(avg_response),
        "today_conversations": today_count,
    })


@client_conversations_bp.route("/conversations/list", methods=["GET"])
@tenant_required
def list_conversations():
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 5))
    date_filter = request.args.get("date_filter", "all")

    rows = _build_exchange_rows(g.business_id, date_filter=date_filter)

    total = len(rows)
    start = (page - 1) * per_page
    page_rows = rows[start:start + per_page]

    return success({
        "conversations": page_rows,
        "pagination": {"page": page, "per_page": per_page, "total": total},
    })


@client_conversations_bp.route("/conversations/<int:conv_id>/messages", methods=["GET"])
@tenant_required
def conversation_messages(conv_id):
    conversation = Conversation.query.filter_by(id=conv_id, business_id=g.business_id).first_or_404()
    messages = Message.query.filter_by(conversation_id=conversation.id).order_by(Message.created_at).all()
    return success({"messages": [
        {"sender": m.sender, "content": m.content, "created_at": m.created_at.isoformat()} for m in messages
    ]})


@client_conversations_bp.route("/conversations/search", methods=["POST"])
@tenant_required
def search_conversations():
    query_text = (request.get_json(silent=True) or {}).get("query", "").lower().strip()
    rows = _build_exchange_rows(g.business_id, date_filter="all")

    if query_text:
        rows = [
            r for r in rows
            if query_text in (r["message"] or "").lower()
            or query_text in (r["ai_response"] or "").lower()
            or query_text in (r["customer_phone"] or "").lower()
        ]

    return success({"conversations": rows})


@client_conversations_bp.route("/conversations/export", methods=["GET"])
@tenant_required
def export_conversations():
    rows = _build_exchange_rows(g.business_id, date_filter="all")
    csv_rows = [
        (r["timestamp"], r["customer_phone"], r["message"], r["ai_response"],
         "Voice" if r["message_type"] == "voice" else "Text", r["response_time_ms"])
        for r in rows
    ]
    return stream_csv(
        csv_rows,
        headers=["Timestamp", "Customer Phone", "Message", "AI Response", "Type", "Response Time (ms)"],
        filename="conversations.csv",
    )
"""Tenant-scoped analytics summary."""
from datetime import datetime, timedelta
from flask import Blueprint, g
from sqlalchemy import func
from app.extensions import db
from app.models.conversation import Conversation
from app.middleware.tenant_guard import tenant_required
from app.utils.responses import success

client_analytics_bp = Blueprint("client_analytics", __name__)


@client_analytics_bp.route("/analytics/summary/<int:business_id>", methods=["GET"])
@tenant_required
def summary(business_id):
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    bid = g.business_id

    total_conversations = db.session.query(func.count(Conversation.id)).filter(
        Conversation.business_id == bid
    ).scalar() or 0

    unique_customers = db.session.query(func.count(func.distinct(Conversation.customer_phone))).filter(
        Conversation.business_id == bid
    ).scalar() or 0

    return success({
        "total_conversations": total_conversations,
        "unique_customers": unique_customers,
        "avg_response_time": None,   # TODO: compute from message timestamps
        "accuracy_rate": None,       # TODO: needs a feedback/rating mechanism
    })

"""Platform-wide analytics: total API calls, latency, trends."""
from datetime import datetime, timedelta
from flask import Blueprint
from sqlalchemy import func
from app.extensions import db
from app.models.api_request_log import ApiRequestLog
from app.models.conversation import Conversation
from app.models.business import Business
from app.middleware.admin_guard import admin_required
from app.utils.responses import success

admin_analytics_bp = Blueprint("admin_analytics", __name__)


@admin_analytics_bp.route("/analytics/data", methods=["GET"])
@admin_required
def analytics_data():
    total_calls = db.session.query(func.count(ApiRequestLog.id)).scalar() or 0
    avg_latency = db.session.query(func.avg(ApiRequestLog.response_time_ms)).scalar() or 0
    return success({"total_api_calls": total_calls, "avg_response_time_ms": round(avg_latency)})


@admin_analytics_bp.route("/platform/trends", methods=["GET"])
@admin_required
def platform_trends():
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)

    conv_rows = (
        db.session.query(func.date(Conversation.started_at), func.count(Conversation.id))
        .filter(Conversation.started_at >= thirty_days_ago)
        .group_by(func.date(Conversation.started_at)).all()
    )
    biz_rows = (
        db.session.query(func.date(Business.created_at), func.count(Business.id))
        .filter(Business.created_at >= thirty_days_ago)
        .group_by(func.date(Business.created_at)).all()
    )
    top_businesses = (
        db.session.query(Business.business_name, func.count(Conversation.id).label("cnt"))
        .join(Conversation, Conversation.business_id == Business.id)
        .group_by(Business.id).order_by(func.count(Conversation.id).desc()).limit(5).all()
    )

    return success({
        "daily_conversations": [{"date": str(d), "count": c} for d, c in conv_rows],
        "daily_new_businesses": [{"date": str(d), "count": c} for d, c in biz_rows],
        "top_businesses": [{"name": n, "conversations": c} for n, c in top_businesses],
    })

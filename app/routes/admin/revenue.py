"""Platform revenue metrics."""
from flask import Blueprint
from app.middleware.admin_guard import admin_required
from app.services.billing_service import revenue_metrics
from app.utils.responses import success

admin_revenue_bp = Blueprint("admin_revenue", __name__)


@admin_revenue_bp.route("/revenue/metrics", methods=["GET"])
@admin_required
def metrics():
    data = revenue_metrics()
    data["insights"] = {
        "trend": "Computed live from active subscriptions",
        "plan_dist": "Group active subs by plan_id for a breakdown",
    }
    return success(data)

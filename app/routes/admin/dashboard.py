"""Platform-wide dashboard summary (replaces the old misnamed ws-telemetry)."""
from flask import Blueprint
from app.middleware.admin_guard import admin_required
from app.services.analytics_service import platform_dashboard_summary
from app.utils.responses import success

admin_dashboard_bp = Blueprint("admin_dashboard", __name__)


@admin_dashboard_bp.route("/dashboard/summary", methods=["GET"])
@admin_required
def summary():
    return success(platform_dashboard_summary())

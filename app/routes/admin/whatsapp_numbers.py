"""
Admin oversight of WhatsApp connections. Since each client now connects their OWN
WABA via Embedded Signup, admin does NOT manually fill in phone_number_id anymore
-- these routes are for monitoring/troubleshooting, not manual linking.
"""
from flask import Blueprint, request
from app.extensions import db
from app.models.whatsapp_number import WhatsAppNumber
from app.middleware.admin_guard import admin_required
from app.utils.responses import success, error

admin_whatsapp_bp = Blueprint("admin_whatsapp", __name__)


@admin_whatsapp_bp.route("/whatsapp-numbers", methods=["GET"])
@admin_required
def list_numbers():
    business_id = request.args.get("business_id")
    query = WhatsAppNumber.query
    if business_id:
        query = query.filter_by(business_id=business_id)

    numbers = query.all()
    return success({"numbers": [
        {
            "id": n.id, "business_id": n.business_id, "display_number": n.display_number,
            "status": n.status, "verification_status": n.verification_status,
            "daily_message_limit": n.daily_message_limit,
        } for n in numbers
    ]})


@admin_whatsapp_bp.route("/whatsapp-numbers/<int:number_id>", methods=["GET"])
@admin_required
def get_number(number_id):
    n = WhatsAppNumber.query.get_or_404(number_id)
    return success({
        "id": n.id, "business_id": n.business_id, "phone_number_id": n.phone_number_id,
        "waba_id": n.waba_id, "status": n.status, "verification_status": n.verification_status,
        "connected_at": n.connected_at.isoformat() if n.connected_at else None,
    })


@admin_whatsapp_bp.route("/whatsapp-numbers/<int:number_id>/toggle", methods=["POST"])
@admin_required
def toggle_number(number_id):
    n = WhatsAppNumber.query.get_or_404(number_id)
    n.status = "disconnected" if n.status == "connected" else "connected"
    db.session.commit()
    return success({"status": n.status})


@admin_whatsapp_bp.route("/whatsapp-numbers/<int:number_id>/force-reconnect", methods=["POST"])
@admin_required
def force_reconnect(number_id):
    """Flags a dead-token connection so the client sees a 'reconnect required' prompt."""
    n = WhatsAppNumber.query.get_or_404(number_id)
    n.status = "error"
    db.session.commit()
    return success(message="Client flagged for reconnection")


@admin_whatsapp_bp.route("/whatsapp-numbers/<int:number_id>", methods=["DELETE"])
@admin_required
def delete_number(number_id):
    n = WhatsAppNumber.query.get_or_404(number_id)
    db.session.delete(n)
    db.session.commit()
    return success(message="Number deregistered")

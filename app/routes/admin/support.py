"""Support ticket CRUD + reply thread. Resolve is a status update, NOT a delete."""
from flask import Blueprint, request
from app.extensions import db
from app.models.support_ticket import SupportTicket, TicketReply
from app.models.business import Business
from app.middleware.admin_guard import admin_required
from app.utils.responses import success, error

admin_support_bp = Blueprint("admin_support", __name__)


@admin_support_bp.route("/support/tickets", methods=["GET"])
@admin_required
def list_tickets():
    status = request.args.get("status")
    priority = request.args.get("priority")

    query = SupportTicket.query
    if status:
        query = query.filter_by(status=status)
    if priority:
        query = query.filter_by(priority=priority)

    tickets = query.order_by(SupportTicket.created_at.desc()).all()

    # Bulk-fetch business names in one query instead of N+1 lookups per ticket
    business_ids = {t.business_id for t in tickets if t.business_id}
    businesses = {b.id: b.business_name for b in Business.query.filter(Business.id.in_(business_ids)).all()}

    return success({"tickets": [
        {
            "id": t.id, "business": businesses.get(t.business_id, f"Business #{t.business_id}"),
            "subject": t.subject, "status": t.status, "priority": t.priority,
            "created": t.created_at.strftime("%Y-%m-%d"),
        } for t in tickets
    ]})


@admin_support_bp.route("/support/tickets/<int:ticket_id>", methods=["GET"])
@admin_required
def get_ticket(ticket_id):
    t = SupportTicket.query.get_or_404(ticket_id)
    replies = TicketReply.query.filter_by(ticket_id=t.id).order_by(TicketReply.created_at).all()
    return success({
        "id": t.id, "subject": t.subject, "description": t.description,
        "status": t.status, "priority": t.priority,
        "replies": [{"sender": r.sender, "message": r.message} for r in replies],
    })


@admin_support_bp.route("/support/tickets", methods=["POST"])
@admin_required
def create_ticket():
    body = request.get_json(silent=True) or {}
    ticket = SupportTicket(
        business_id=body.get("business_id"),
        subject=body.get("subject"),
        description=body.get("description"),
        priority=body.get("priority", "medium"),
    )
    db.session.add(ticket)
    db.session.commit()
    return success({"id": ticket.id}, "Ticket created", 201)


@admin_support_bp.route("/support/tickets/<int:ticket_id>", methods=["PUT"])
@admin_required
def update_ticket(ticket_id):
    body = request.get_json(silent=True) or {}
    t = SupportTicket.query.get_or_404(ticket_id)
    t.priority = body.get("priority", t.priority)
    t.status = body.get("status", t.status)
    db.session.commit()
    return success(message="Ticket updated")


@admin_support_bp.route("/support/tickets/<int:ticket_id>/resolve", methods=["POST"])
@admin_required
def resolve_ticket(ticket_id):
    """Status update -- NOT a DELETE. History is preserved for audit."""
    t = SupportTicket.query.get_or_404(ticket_id)
    t.status = "resolved"
    t.resolved_at = db.func.now()
    db.session.commit()
    return success(message="Ticket resolved")


@admin_support_bp.route("/support/tickets/<int:ticket_id>/reply", methods=["POST"])
@admin_required
def reply_ticket(ticket_id):
    message = (request.get_json(silent=True) or {}).get("message")
    if not message:
        return error("message required")

    reply = TicketReply(ticket_id=ticket_id, sender="admin", message=message)
    db.session.add(reply)
    db.session.commit()
    return success({"id": reply.id}, "Reply added", 201)


@admin_support_bp.route("/support/tickets/<int:ticket_id>", methods=["DELETE"])
@admin_required
def delete_ticket(ticket_id):
    """Rare -- prefer resolve() over this."""
    TicketReply.query.filter_by(ticket_id=ticket_id).delete()
    SupportTicket.query.filter_by(id=ticket_id).delete()
    db.session.commit()
    return success(message="Ticket hard-deleted")
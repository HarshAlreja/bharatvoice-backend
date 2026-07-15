"""Client-facing billing: subscription, invoices, plan change."""
from flask import Blueprint, request, g
from app.models.subscription import Subscription
from app.models.plan import Plan
from app.models.invoice import Invoice
from app.middleware.tenant_guard import tenant_required
from app.utils.responses import success, error

client_billing_bp = Blueprint("client_billing", __name__)


@client_billing_bp.route("/billing/subscription/<int:business_id>", methods=["GET"])
@tenant_required
def get_subscription(business_id):
    sub = Subscription.query.filter_by(business_id=g.business_id, status="active").first()
    if not sub:
        return success({"subscription": None})

    plan = Plan.query.get(sub.plan_id)
    return success({"plan_name": plan.name, "amount": float(sub.amount), "billing_cycle": sub.billing_cycle})


@client_billing_bp.route("/billing/invoices/<int:business_id>", methods=["GET"])
@tenant_required
def list_invoices(business_id):
    invoices = Invoice.query.filter_by(business_id=g.business_id).order_by(Invoice.invoice_date.desc()).all()
    return success({"invoices": [
        {"id": i.id, "amount": float(i.amount), "status": i.status, "invoice_date": i.invoice_date.isoformat()}
        for i in invoices
    ]})


@client_billing_bp.route("/subscription/change-plan/<int:business_id>", methods=["POST"])
@tenant_required
def change_plan(business_id):
    from app.extensions import db

    plan_id = (request.get_json(silent=True) or {}).get("plan_id")
    plan = Plan.query.get(plan_id)
    if not plan:
        return error("Invalid plan", 404)

    sub = Subscription.query.filter_by(business_id=g.business_id, status="active").first()
    if not sub:
        return error("No active subscription", 404)

    sub.plan_id = plan.id
    sub.amount = plan.monthly_price
    db.session.commit()
    return success(message="Plan updated")

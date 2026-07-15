"""Subscription CRUD -- assigns/changes a business's plan, drives billing."""
from flask import Blueprint, request
from datetime import datetime
from app.extensions import db
from app.models.subscription import Subscription
from app.models.plan import Plan
from app.middleware.admin_guard import admin_required
from app.utils.responses import success, error

admin_subscriptions_bp = Blueprint("admin_subscriptions", __name__)


@admin_subscriptions_bp.route("/subscriptions", methods=["GET"])
@admin_required
def list_subscriptions():
    business_id = request.args.get("business_id")
    status = request.args.get("status")

    query = Subscription.query
    if business_id:
        query = query.filter_by(business_id=business_id)
    if status:
        query = query.filter_by(status=status)

    subs = query.all()
    return success({"subscriptions": [
        {"id": s.id, "business_id": s.business_id, "plan_id": s.plan_id, "status": s.status,
         "amount": float(s.amount or 0), "billing_cycle": s.billing_cycle}
        for s in subs
    ]})


@admin_subscriptions_bp.route("/subscriptions/<int:sub_id>", methods=["GET"])
@admin_required
def get_subscription(sub_id):
    s = Subscription.query.get_or_404(sub_id)
    return success({
        "id": s.id, "business_id": s.business_id, "plan_id": s.plan_id, "status": s.status,
        "amount": float(s.amount or 0), "next_billing_at": s.next_billing_at.isoformat() if s.next_billing_at else None,
    })


@admin_subscriptions_bp.route("/subscriptions", methods=["POST"])
@admin_required
def create_subscription():
    body = request.get_json(silent=True) or {}
    plan = Plan.query.get(body.get("plan_id"))
    if not plan:
        return error("Invalid plan_id", 404)

    sub = Subscription(
        business_id=body.get("business_id"), plan_id=plan.id,
        amount=plan.monthly_price, billing_cycle=body.get("billing_cycle", "monthly"),
    )
    db.session.add(sub)
    db.session.commit()
    return success({"id": sub.id}, "Subscription created", 201)


@admin_subscriptions_bp.route("/subscriptions/<int:sub_id>", methods=["PUT"])
@admin_required
def update_subscription(sub_id):
    body = request.get_json(silent=True) or {}
    s = Subscription.query.get_or_404(sub_id)
    s.plan_id = body.get("plan_id", s.plan_id)
    s.billing_cycle = body.get("billing_cycle", s.billing_cycle)
    db.session.commit()
    return success(message="Subscription updated")


@admin_subscriptions_bp.route("/subscriptions/<int:sub_id>", methods=["DELETE"])
@admin_required
def cancel_subscription(sub_id):
    s = Subscription.query.get_or_404(sub_id)
    s.status = "cancelled"
    s.cancelled_at = datetime.utcnow()
    db.session.commit()
    return success(message="Subscription cancelled")


@admin_subscriptions_bp.route("/subscriptions/<int:sub_id>/renew", methods=["POST"])
@admin_required
def renew_subscription(sub_id):
    from dateutil.relativedelta import relativedelta

    s = Subscription.query.get_or_404(sub_id)
    months = 1 if s.billing_cycle == "monthly" else 12
    s.next_billing_at = (s.next_billing_at or datetime.utcnow()) + relativedelta(months=months)
    db.session.commit()
    return success(message="Subscription renewed")

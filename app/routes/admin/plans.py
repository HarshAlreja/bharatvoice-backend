"""Subscription plan CRUD."""
from flask import Blueprint, request
from app.extensions import db
from app.models.plan import Plan
from app.middleware.admin_guard import admin_required
from app.utils.responses import success, error

admin_plans_bp = Blueprint("admin_plans", __name__)


@admin_plans_bp.route("/plans", methods=["GET"])
@admin_required
def list_plans():
    plans = Plan.query.all()
    return success({"plans": [
        {"id": p.id, "name": p.name, "monthly_price": float(p.monthly_price or 0), "is_active": p.is_active}
        for p in plans
    ]})


@admin_plans_bp.route("/plans/<int:plan_id>", methods=["GET"])
@admin_required
def get_plan(plan_id):
    p = Plan.query.get_or_404(plan_id)
    return success({
        "id": p.id, "name": p.name, "monthly_price": float(p.monthly_price or 0),
        "yearly_price": float(p.yearly_price or 0), "token_limit": p.token_limit,
        "whatsapp_number_limit": p.whatsapp_number_limit, "features": p.features_json,
    })


@admin_plans_bp.route("/plans", methods=["POST"])
@admin_required
def create_plan():
    body = request.get_json(silent=True) or {}
    plan = Plan(
        name=body.get("name"), monthly_price=body.get("monthly_price"),
        yearly_price=body.get("yearly_price"), token_limit=body.get("token_limit"),
        whatsapp_number_limit=body.get("whatsapp_number_limit", 1),
        features_json=body.get("features", {}),
    )
    db.session.add(plan)
    db.session.commit()
    return success({"id": plan.id}, "Plan created", 201)


@admin_plans_bp.route("/plans/<int:plan_id>", methods=["PUT"])
@admin_required
def update_plan(plan_id):
    body = request.get_json(silent=True) or {}
    p = Plan.query.get_or_404(plan_id)
    p.name = body.get("name", p.name)
    p.monthly_price = body.get("monthly_price", p.monthly_price)
    p.yearly_price = body.get("yearly_price", p.yearly_price)
    db.session.commit()
    return success(message="Plan updated")


@admin_plans_bp.route("/plans/<int:plan_id>", methods=["DELETE"])
@admin_required
def retire_plan(plan_id):
    p = Plan.query.get_or_404(plan_id)
    p.is_active = False  # soft-delete, don't break active subscriptions
    db.session.commit()
    return success(message="Plan retired")

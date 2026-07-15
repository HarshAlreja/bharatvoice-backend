"""Full CRUD on tenants, cross-tenant (no business_id filter -- admin sees everything)."""
from flask import Blueprint, request
from app.extensions import db
from app.models.business import Business
from app.models.user import User
from app.models.document import Document
from app.models.conversation import Conversation
from app.middleware.admin_guard import admin_required, super_admin_required
from app.utils.pagination import paginate_query
from app.utils.responses import success, error

admin_businesses_bp = Blueprint("admin_businesses", __name__)


def _serialize(b: Business):
    doc_count = Document.query.filter_by(business_id=b.id).count()
    conv_count = Conversation.query.filter_by(business_id=b.id).count()
    return {
        "id": b.id,
        "business_name": b.business_name,
        "owner": {"name": b.owner.name, "email": b.owner.email} if b.owner else None,
        "status": b.status,
        "industry": b.industry,
        "total_documents": doc_count,
        "conversations_last_30_days": conv_count,
    }


@admin_businesses_bp.route("/businesses", methods=["GET"])
@admin_required
def list_businesses():
    search = request.args.get("search", "")
    page = request.args.get("page", 1)
    per_page = request.args.get("per_page", 50)

    query = Business.query.filter(Business.deleted_at.is_(None))
    if search:
        query = query.join(User, Business.owner_id == User.id).filter(
            db.or_(
                Business.business_name.ilike(f"%{search}%"),
                User.name.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%"),
            )
        )

    items, meta = paginate_query(query, page=page, per_page=per_page)
    return success({"businesses": [_serialize(b) for b in items], "pagination": meta})


@admin_businesses_bp.route("/businesses/<int:business_id>", methods=["GET"])
@admin_required
def get_business(business_id):
    b = Business.query.get_or_404(business_id)
    return success(_serialize(b))


@admin_businesses_bp.route("/businesses", methods=["POST"])
@admin_required
def create_business():
    body = request.get_json(silent=True) or {}
    owner = User.query.get(body.get("owner_id"))
    if not owner:
        return error("owner_id not found", 404)

    business = Business(
        business_name=body.get("business_name"),
        owner_id=owner.id,
        industry=body.get("industry"),
        status="pending",
    )
    db.session.add(business)
    db.session.commit()
    return success(_serialize(business), "Business created", 201)


@admin_businesses_bp.route("/businesses/<int:business_id>", methods=["PUT"])
@admin_required
def update_business(business_id):
    body = request.get_json(silent=True) or {}
    business = Business.query.get_or_404(business_id)
    business.business_name = body.get("business_name", business.business_name)
    business.industry = body.get("industry", business.industry)
    db.session.commit()
    return success(_serialize(business), "Business updated")


@admin_businesses_bp.route("/businesses/<int:business_id>", methods=["DELETE"])
@super_admin_required
def delete_business(business_id):
    business = Business.query.get_or_404(business_id)
    business.deleted_at = db.func.now()  # soft delete
    db.session.commit()
    return success(message="Business soft-deleted")


@admin_businesses_bp.route("/business/<int:business_id>/status", methods=["POST"])
@admin_required
def update_status(business_id):
    new_status = (request.get_json(silent=True) or {}).get("status")
    if new_status not in ("active", "suspended", "pending"):
        return error("Invalid status")

    business = Business.query.get_or_404(business_id)
    business.status = new_status
    db.session.commit()
    return success(message=f"Status updated to {new_status}")


@admin_businesses_bp.route("/business/<int:business_id>/usage", methods=["GET"])
@admin_required
def business_usage(business_id):
    from app.models.token_usage_log import TokenUsageLog

    tokens = db.session.query(db.func.sum(TokenUsageLog.tokens_used)).filter_by(
        business_id=business_id
    ).scalar() or 0
    docs = Document.query.filter_by(business_id=business_id).count()
    convs = Conversation.query.filter_by(business_id=business_id).count()

    return success({"total_tokens": tokens, "total_documents": docs, "total_conversations": convs})

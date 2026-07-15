"""CRUD on client-side users (business owners/staff), cross-tenant."""
from flask import Blueprint, request
from app.extensions import db
from app.models.user import User
from app.middleware.admin_guard import admin_required
from app.utils.security import hash_password
from app.utils.pagination import paginate_query
from app.utils.responses import success, error

admin_users_bp = Blueprint("admin_users", __name__)


@admin_users_bp.route("/users", methods=["GET"])
@admin_required
def list_users():
    search = request.args.get("search", "")
    page = request.args.get("page", 1)

    query = User.query
    if search:
        query = query.filter(db.or_(User.name.ilike(f"%{search}%"), User.email.ilike(f"%{search}%")))

    items, meta = paginate_query(query, page=page)
    return success({
        "users": [{"id": u.id, "name": u.name, "email": u.email, "business_id": u.business_id,
                    "is_active": u.is_active} for u in items],
        "pagination": meta,
    })


@admin_users_bp.route("/users/<int:user_id>", methods=["GET"])
@admin_required
def get_user(user_id):
    u = User.query.get_or_404(user_id)
    return success({"id": u.id, "name": u.name, "email": u.email, "business_id": u.business_id})


@admin_users_bp.route("/users", methods=["POST"])
@admin_required
def create_user():
    body = request.get_json(silent=True) or {}
    if User.query.filter_by(email=body.get("email")).first():
        return error("Email already exists")

    user = User(
        name=body.get("name"),
        email=body.get("email"),
        password_hash=hash_password(body.get("password", "changeme123")),
        business_id=body.get("business_id"),
    )
    db.session.add(user)
    db.session.commit()
    return success({"id": user.id}, "User created", 201)


@admin_users_bp.route("/users/<int:user_id>", methods=["PUT"])
@admin_required
def update_user(user_id):
    body = request.get_json(silent=True) or {}
    user = User.query.get_or_404(user_id)
    user.name = body.get("name", user.name)
    user.email = body.get("email", user.email)
    db.session.commit()
    return success(message="User updated")


@admin_users_bp.route("/users/<int:user_id>", methods=["DELETE"])
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_active = False
    db.session.commit()
    return success(message="User deactivated")


@admin_users_bp.route("/users/<int:user_id>/reset-password", methods=["PUT"])
@admin_required
def reset_password(user_id):
    new_password = (request.get_json(silent=True) or {}).get("password", "changeme123")
    user = User.query.get_or_404(user_id)
    user.password_hash = hash_password(new_password)
    db.session.commit()
    return success(message="Password reset")

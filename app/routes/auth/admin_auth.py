"""Admin login only -- admin accounts are created manually/seeded, not self-signup."""
from flask import Blueprint, request
from flask_jwt_extended import create_access_token
from app.models.admin import Admin
from app.utils.security import verify_password
from app.utils.responses import success, error

admin_auth_bp = Blueprint("admin_auth", __name__)


@admin_auth_bp.route("/admin-login", methods=["POST"])
def admin_login():
    body = request.get_json(silent=True) or {}
    email = body.get("email", "").lower().strip()
    password = body.get("password")

    admin = Admin.query.filter_by(email=email, is_active=True).first()
    if not admin or not verify_password(password, admin.password_hash):
        return error("Invalid admin credentials", 401)

    token = create_access_token(identity=str(admin.id), additional_claims={
        "actor_type": "admin",
        "role": admin.role,
    })

    return success({
        "user": {"id": admin.id, "name": admin.name, "email": admin.email, "role": admin.role},
        "tokens": {"access_token": token},
    })

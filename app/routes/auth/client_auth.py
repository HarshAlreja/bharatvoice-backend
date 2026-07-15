"""Client-side signup, OTP verify, login, approval status polling."""
from flask import Blueprint, request
from flask_jwt_extended import create_access_token
from app.extensions import db
from app.models.user import User
from app.models.business import Business
from app.utils.security import hash_password, verify_password
from app.utils.validators import is_valid_email
from app.utils.responses import success, error
from app.services.otp_service import generate_and_send_otp, verify_otp

client_auth_bp = Blueprint("client_auth", __name__)


@client_auth_bp.route("/signup", methods=["POST"])
def signup():
    body = request.get_json(silent=True) or {}
    full_name = body.get("full_name")
    email = body.get("email", "").lower().strip()
    password = body.get("password")
    business_name = body.get("business_name")

    if not all([full_name, email, password, business_name]):
        return error("All fields are required")
    if not is_valid_email(email):
        return error("Invalid email")
    if User.query.filter_by(email=email).first():
        return error("Email already registered")

    user = User(name=full_name, email=email, password_hash=hash_password(password))
    db.session.add(user)
    db.session.flush()

    business = Business(business_name=business_name, owner_id=user.id, status="pending")
    db.session.add(business)
    db.session.flush()

    user.business_id = business.id
    db.session.commit()

    generate_and_send_otp(email, purpose="signup")

    return success({"user": {"id": user.id, "email": user.email}}, "Signup successful, check your email for the code")


@client_auth_bp.route("/send-otp", methods=["POST"])
def send_otp():
    print("sending email")
    email = (request.get_json(silent=True) or {}).get("email", "").lower().strip()
    if not is_valid_email(email):
        return error("Invalid email")
    generate_and_send_otp(email, purpose="signup")
    return success(message="Code sent")


@client_auth_bp.route("/verify-otp", methods=["POST"])
def verify_otp_route():
    body = request.get_json(silent=True) or {}
    email = body.get("email", "").lower().strip()
    code = body.get("verification_code")

    if not verify_otp(email, code, purpose="signup"):
        return error("Invalid or expired code")

    user = User.query.filter_by(email=email).first()
    if not user:
        return error("User not found", 404)

    business = None
    if user.business_id:
        business = Business.query.get(user.business_id)
        business.email_verified = True
        db.session.commit()

    # Issue a token now -- signup doesn't log the user in, but pending_approval.html
    # needs to poll check-status right after this step, so they must already be
    # authenticated by the time they land there.
    token = create_access_token(identity=str(user.id), additional_claims={
        "actor_type": "client",
        "business_id": user.business_id,
    })

    return success({
        "user": {
            "id": user.id, "name": user.name, "email": user.email,
            "business_id": user.business_id,
            "status": business.status if business else "pending",
        },
        "tokens": {"access_token": token},
    }, "Email verified, awaiting admin approval")


@client_auth_bp.route("/login", methods=["POST"])
def login():
    body = request.get_json(silent=True) or {}
    email = body.get("email", "").lower().strip()
    password = body.get("password")

    user = User.query.filter_by(email=email).first()
    if not user or not verify_password(password, user.password_hash):
        return error("Invalid credentials", 401)

    business = Business.query.get(user.business_id) if user.business_id else None

    token = create_access_token(identity=str(user.id), additional_claims={
        "actor_type": "client",
        "business_id": user.business_id,
    })

    return success({
        "user": {
            "id": user.id, "name": user.name, "email": user.email,
            "business_id": user.business_id,
            "status": business.status if business else "pending",
        },
        "tokens": {"access_token": token},
    })


@client_auth_bp.route("/check-status", methods=["GET"])
def check_status():
    from flask_jwt_extended import verify_jwt_in_request, get_jwt

    verify_jwt_in_request()
    claims = get_jwt()
    business = Business.query.get(claims.get("business_id"))
    if not business:
        return error("Business not found", 404)

    return success({"status": business.status, "is_approved": business.status == "active"})
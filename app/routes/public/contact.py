"""Public contact form (optional feature)."""
from flask import Blueprint, request
from app.extensions import db
from app.models.contact_submission import ContactSubmission
from app.utils.responses import success, error
from app.utils.validators import is_valid_email

contact_bp = Blueprint("contact", __name__)


@contact_bp.route("/contact", methods=["POST"])
def submit_contact():
    body = request.get_json(silent=True) or {}
    email = body.get("email", "")

    if not is_valid_email(email):
        return error("Invalid email")

    submission = ContactSubmission(
        name=body.get("name"), email=email,
        subject=body.get("subject"), message=body.get("message"),
    )
    db.session.add(submission)
    db.session.commit()
    return success(message="Message received")

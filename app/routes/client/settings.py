"""Tenant settings: business info, password, irreversible purge."""
from flask import Blueprint, request, g
from app.extensions import db
from app.models.business import Business
from app.models.user import User
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.conversation import Conversation
from app.models.whatsapp_number import WhatsAppNumber
from app.middleware.tenant_guard import tenant_required
from app.utils.security import hash_password
from app.vectorstore.faiss_manager import delete_business_index
from app.utils.responses import success, error

client_settings_bp = Blueprint("client_settings", __name__)


@client_settings_bp.route("/settings/tenant/<int:business_id>", methods=["GET"])
@tenant_required
def get_settings(business_id):
    business = Business.query.get_or_404(g.business_id)
    return success({"business_name": business.business_name, "industry": business.industry})


@client_settings_bp.route("/settings/update/<int:business_id>", methods=["PUT"])
@tenant_required
def update_settings(business_id):
    body = request.get_json(silent=True) or {}
    business = Business.query.get_or_404(g.business_id)
    business.business_name = body.get("business_name", business.business_name)
    business.industry = body.get("industry", business.industry)
    db.session.commit()
    return success(message="Settings updated")


@client_settings_bp.route("/settings/update-password/<int:business_id>", methods=["PUT"])
@tenant_required
def update_password(business_id):
    password = (request.get_json(silent=True) or {}).get("password")
    if not password or len(password) < 8:
        return error("Password must be at least 8 characters")

    business = Business.query.get_or_404(g.business_id)
    business.owner.password_hash = hash_password(password)
    db.session.commit()
    return success(message="Password updated")


@client_settings_bp.route("/tenant/purge/<int:business_id>", methods=["DELETE"])
@tenant_required
def purge_tenant(business_id):
    """Irreversible. Should require a re-auth confirmation step on the frontend."""
    bid = g.business_id

    doc_ids = [d.id for d in Document.query.filter_by(business_id=bid).all()]
    DocumentChunk.query.filter(DocumentChunk.document_id.in_(doc_ids)).delete(synchronize_session=False)
    Document.query.filter_by(business_id=bid).delete()
    Conversation.query.filter_by(business_id=bid).delete()
    WhatsAppNumber.query.filter_by(business_id=bid).delete()
    delete_business_index(bid)

    business = Business.query.get(bid)
    business.deleted_at = db.func.now()
    business.status = "suspended"
    db.session.commit()

    return success(message="Tenant purged")

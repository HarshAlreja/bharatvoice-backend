"""Cross-tenant document oversight."""
from flask import Blueprint, request
from app.extensions import db
from app.models.document import Document
from app.middleware.admin_guard import admin_required
from app.services.embedding_service import EmbeddingService
from app.utils.responses import success, error

admin_documents_bp = Blueprint("admin_documents", __name__)


@admin_documents_bp.route("/documents", methods=["GET"])
@admin_required
def list_documents():
    business_id = request.args.get("business_id")
    query = Document.query
    if business_id:
        query = query.filter_by(business_id=business_id)

    docs = query.order_by(Document.created_at.desc()).limit(200).all()
    return success({"documents": [
        {"id": d.id, "business_id": d.business_id, "filename": d.filename,
         "status": d.status, "error_message": d.error_message}
        for d in docs
    ]})


@admin_documents_bp.route("/documents/<int:doc_id>", methods=["DELETE"])
@admin_required
def delete_document(doc_id):
    doc = Document.query.get_or_404(doc_id)
    EmbeddingService().delete_document_embeddings(doc.business_id, doc_id)
    db.session.delete(doc)
    db.session.commit()
    return success(message="Document force-removed")


@admin_documents_bp.route("/documents/<int:doc_id>/reprocess", methods=["POST"])
@admin_required
def reprocess_document(doc_id):
    doc = Document.query.get_or_404(doc_id)
    if not doc.file_path:
        return error("No stored file_path for this document -- can't reprocess, ask the owner to re-upload", 400)

    EmbeddingService().delete_document_embeddings(doc.business_id, doc_id)

    result = EmbeddingService().process_document(
        business_id=doc.business_id,
        document_id=doc.id,
        file_path=doc.file_path,
        file_type=doc.file_type,
        original_filename=doc.filename,
        file_size_bytes=doc.file_size or 0,
    )

    if result["status"] != "success":
        return error(result.get("error_message", "Reprocessing failed"), 500)

    return success({"chunk_count": doc.chunk_count}, "Reprocessing complete")

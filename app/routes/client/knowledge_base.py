"""
Document upload / list / delete.

Upload now saves the raw file to disk first, then hands off to
EmbeddingService.process_document() for the FULL pipeline (validate, extract,
hash, detect language, chunk, embed, store in FAISS, write document_chunks).
document_processor.py has been retired -- it was a duplicate subset of what
EmbeddingService already does end-to-end. Don't reintroduce it.
"""
import os
from flask import Blueprint, request, g
from app.extensions import db
from app.models.document import Document
from app.middleware.tenant_guard import tenant_required
from app.services.embedding_service import EmbeddingService
from app.utils.responses import success, error

client_kb_bp = Blueprint("client_kb", __name__)

UPLOAD_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")


def _business_upload_dir(business_id: int) -> str:
    path = os.path.join(UPLOAD_ROOT, str(business_id))
    os.makedirs(path, exist_ok=True)
    return path


@client_kb_bp.route("/knowledge-base/documents/<int:business_id>", methods=["GET"])
@tenant_required
def list_documents(business_id):
    docs = Document.query.filter_by(business_id=g.business_id).order_by(Document.created_at.desc()).all()
    return success({"documents": [
        {
            "id": d.id, "filename": d.filename, "file_type": d.file_type,
            "status": d.status, "chunk_count": d.chunk_count,
            "error_message": d.error_message, "file_size": d.file_size,
            "created_at": d.created_at.isoformat(),
        }
        for d in docs
    ]})


@client_kb_bp.route("/knowledge-base/upload/<int:business_id>", methods=["POST"])
@tenant_required
def upload_document(business_id):
    file = request.files.get("file")
    if not file or not file.filename:
        return error("No file uploaded")

    filename = file.filename
    file_type = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    file_bytes = file.read()
    file_size = len(file_bytes)

    # Save to disk -- EmbeddingService reads from a file_path, not raw bytes,
    # because it needs to re-open the file for corruption checks, hashing, etc.
    save_dir = _business_upload_dir(g.business_id)
    saved_path = os.path.join(save_dir, filename)
    with open(saved_path, "wb") as f:
        f.write(file_bytes)

    document = Document(
        business_id=g.business_id,
        filename=filename,
        file_path=saved_path,
        file_type=file_type,
        file_size=file_size,
        status="processing",
    )
    db.session.add(document)
    db.session.commit()

    result = EmbeddingService().process_document(
        business_id=g.business_id,
        document_id=document.id,
        file_path=saved_path,
        file_type=file_type,
        original_filename=filename,
        file_size_bytes=file_size,
    )

    if result["status"] != "success":
        return error(result.get("error_message", "Processing failed"), 500)

    return success({
        "id": document.id, "status": document.status, "chunk_count": document.chunk_count,
    }, "Document uploaded and indexed")


@client_kb_bp.route("/knowledge-base/document/<int:doc_id>", methods=["DELETE"])
@tenant_required
def delete_document(doc_id):
    document = Document.query.filter_by(id=doc_id, business_id=g.business_id).first()
    if not document:
        return error("Not found", 404)

    EmbeddingService().delete_document_embeddings(g.business_id, doc_id)

    if document.file_path and os.path.exists(document.file_path):
        try:
            os.remove(document.file_path)
        except OSError:
            pass

    db.session.delete(document)
    db.session.commit()
    return success(message="Document deleted")
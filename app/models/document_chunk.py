"""Actual RAG chunks. faiss_vector_id links back to the business's FAISS index position."""
from datetime import datetime
from app.extensions import db


class DocumentChunk(db.Model):
    __tablename__ = "document_chunks"

    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey("documents.id"), nullable=False)
    business_id = db.Column(db.Integer, db.ForeignKey("businesses.id"), nullable=False)  # denormalized for speed
    chunk_text = db.Column(db.Text, nullable=False)
    chunk_index = db.Column(db.Integer)
    faiss_vector_id = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

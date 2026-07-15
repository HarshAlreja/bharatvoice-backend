"""Knowledge-base documents uploaded per business."""
from datetime import datetime
from app.extensions import db


class Document(db.Model):
    __tablename__ = "documents"

    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey("businesses.id"), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500))  # where the raw file lives on disk, needed for (re)processing
    file_type = db.Column(db.String(20))
    file_size = db.Column(db.Integer)
    status = db.Column(db.String(20), default="processing")  # processing | indexed | failed
    error_message = db.Column(db.Text, nullable=True)
    chunk_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

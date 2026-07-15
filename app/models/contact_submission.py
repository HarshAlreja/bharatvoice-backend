"""Public contact form submissions (optional feature)."""
from datetime import datetime
from app.extensions import db


class ContactSubmission(db.Model):
    __tablename__ = "contact_submissions"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120))
    email = db.Column(db.String(120))
    subject = db.Column(db.String(255))
    message = db.Column(db.Text)
    status = db.Column(db.String(20), default="new")  # new | read | replied
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

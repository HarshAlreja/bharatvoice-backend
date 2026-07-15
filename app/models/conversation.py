"""One thread = one end-customer chatting with one business's bot."""
from datetime import datetime
from app.extensions import db


class Conversation(db.Model):
    __tablename__ = "conversations"

    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey("businesses.id"), nullable=False)
    customer_phone = db.Column(db.String(20), nullable=False)
    customer_name = db.Column(db.String(120), nullable=True)
    status = db.Column(db.String(20), default="active")  # active | closed
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    ended_at = db.Column(db.DateTime, nullable=True)

"""Append-only, one row per LLM call. Feeds dashboard + analytics."""
from datetime import datetime
from app.extensions import db


class TokenUsageLog(db.Model):
    __tablename__ = "token_usage_logs"

    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey("businesses.id"), nullable=False)
    conversation_id = db.Column(db.Integer, db.ForeignKey("conversations.id"), nullable=True)
    model_used = db.Column(db.String(50))
    tokens_used = db.Column(db.Integer, default=0)
    cost_estimate = db.Column(db.Numeric(10, 4), default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

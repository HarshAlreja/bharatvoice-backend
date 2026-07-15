"""Subscription tiers."""
from datetime import datetime
from app.extensions import db


class Plan(db.Model):
    __tablename__ = "plans"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    monthly_price = db.Column(db.Numeric(10, 2))
    yearly_price = db.Column(db.Numeric(10, 2))
    token_limit = db.Column(db.Integer)
    whatsapp_number_limit = db.Column(db.Integer, default=1)
    features_json = db.Column(db.JSON)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

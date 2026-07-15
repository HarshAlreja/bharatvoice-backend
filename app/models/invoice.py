"""Billing history."""
from datetime import datetime
from app.extensions import db


class Invoice(db.Model):
    __tablename__ = "invoices"

    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey("businesses.id"), nullable=False)
    subscription_id = db.Column(db.Integer, db.ForeignKey("subscriptions.id"), nullable=False)
    amount = db.Column(db.Numeric(10, 2))
    status = db.Column(db.String(20), default="pending")  # paid | pending | failed
    invoice_date = db.Column(db.DateTime, default=datetime.utcnow)
    paid_at = db.Column(db.DateTime, nullable=True)
    pdf_url = db.Column(db.String(255), nullable=True)

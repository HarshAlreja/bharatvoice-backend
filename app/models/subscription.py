"""Business <-> Plan mapping, billing state."""
from datetime import datetime
from app.extensions import db


class Subscription(db.Model):
    __tablename__ = "subscriptions"

    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey("businesses.id"), nullable=False)
    plan_id = db.Column(db.Integer, db.ForeignKey("plans.id"), nullable=False)
    status = db.Column(db.String(20), default="active")  # active | cancelled | past_due
    amount = db.Column(db.Numeric(10, 2))
    billing_cycle = db.Column(db.String(10), default="monthly")  # monthly | yearly
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    cancelled_at = db.Column(db.DateTime, nullable=True)
    next_billing_at = db.Column(db.DateTime, nullable=True)

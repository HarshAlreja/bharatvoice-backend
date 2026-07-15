"""Support tickets + reply thread."""
from datetime import datetime
from app.extensions import db


class SupportTicket(db.Model):
    __tablename__ = "support_tickets"

    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey("businesses.id"), nullable=False)
    subject = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default="open")  # open | in_progress | resolved
    priority = db.Column(db.String(10), default="medium")  # low | medium | high
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    resolved_at = db.Column(db.DateTime, nullable=True)


class TicketReply(db.Model):
    __tablename__ = "ticket_replies"

    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey("support_tickets.id"), nullable=False)
    sender = db.Column(db.String(20))  # admin | business
    message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

"""Append-only, one row per API request. Purge rows older than 90 days via cron."""
from datetime import datetime
from app.extensions import db


class ApiRequestLog(db.Model):
    __tablename__ = "api_request_logs"

    id = db.Column(db.Integer, primary_key=True)
    endpoint = db.Column(db.String(255))
    method = db.Column(db.String(10))
    status_code = db.Column(db.Integer)
    response_time_ms = db.Column(db.Integer)
    business_id = db.Column(db.Integer, db.ForeignKey("businesses.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

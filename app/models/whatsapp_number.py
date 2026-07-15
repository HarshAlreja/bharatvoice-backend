"""
Each business connects its OWN Meta WhatsApp Business Account (WABA) via Embedded
Signup. access_token is stored PER ROW here, encrypted -- it is NOT shared across
tenants. BharatVoice only holds its own Meta Developer App id/secret (see
PlatformSettings), used solely to exchange each client's signup code for their token.
"""
from datetime import datetime
from app.extensions import db


class WhatsAppNumber(db.Model):
    __tablename__ = "whatsapp_numbers"

    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey("businesses.id"), nullable=False)

    # Filled in automatically after Embedded Signup completes
    phone_number_id = db.Column(db.String(64), unique=True, nullable=True)  # webhook routing key
    waba_id = db.Column(db.String(64), nullable=True)
    meta_business_id = db.Column(db.String(64), nullable=True)
    display_number = db.Column(db.String(20), nullable=True)

    access_token_encrypted = db.Column(db.Text, nullable=True)  # per-tenant, encrypted at rest
    token_expires_at = db.Column(db.DateTime, nullable=True)

    status = db.Column(db.String(20), default="connecting")
    # connecting | connected | disconnected | error

    verification_status = db.Column(db.String(20), default="unverified")
    # unverified | pending | verified

    daily_message_limit = db.Column(db.Integer, default=250)

    connected_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

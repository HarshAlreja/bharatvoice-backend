"""
Singleton config row (id=1). meta_app_id/meta_app_secret are BharatVoice's OWN Meta
Developer App credentials -- a ONE-TIME setup, used only to exchange each client's
Embedded Signup code for THEIR OWN access token. Never a shared WhatsApp token here.
"""
from datetime import datetime
from app.extensions import db


class PlatformSettings(db.Model):
    __tablename__ = "platform_settings"

    id = db.Column(db.Integer, primary_key=True)
    llm_provider = db.Column(db.String(50), default="groq-llama3")
    token_rate_limit = db.Column(db.Integer, default=50000)
    stt_model = db.Column(db.String(50), default="sarvam-v2")

    meta_app_id = db.Column(db.String(64))
    meta_app_secret_encrypted = db.Column(db.Text)
    meta_api_version = db.Column(db.String(20), default="v21.0")
    meta_configuration_id = db.Column(db.String(64))
    meta_webhook_verify_token = db.Column(db.String(255))

    maintenance_mode = db.Column(db.Boolean, default=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

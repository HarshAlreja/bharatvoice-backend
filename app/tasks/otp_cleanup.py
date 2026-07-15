"""Cron job: delete expired/used OTP codes. Run hourly."""
from datetime import datetime
from app.extensions import db
from app.models.otp_code import OtpCode


def run():
    deleted = OtpCode.query.filter(OtpCode.expires_at < datetime.utcnow()).delete()
    db.session.commit()
    print(f"Purged {deleted} expired OTP codes")

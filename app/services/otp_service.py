"""Generate, send, and verify signup OTP codes."""
import random
from datetime import datetime, timedelta
from app.extensions import db
from app.models.otp_code import OtpCode
from app.services.notification_service import send_otp_email


def generate_and_send_otp(email: str, purpose: str = "signup"):
    code = f"{random.randint(0, 999999):06d}"
    otp = OtpCode(
        email=email,
        code=code,
        purpose=purpose,
        expires_at=datetime.utcnow() + timedelta(minutes=10),
    )
    db.session.add(otp)
    db.session.commit()
    send_otp_email(email, code)
    return otp


def verify_otp(email: str, code: str, purpose: str = "signup") -> bool:
    otp = (
        OtpCode.query.filter_by(email=email, code=code, purpose=purpose, verified_at=None)
        .order_by(OtpCode.created_at.desc())
        .first()
    )
    if not otp or otp.expires_at < datetime.utcnow():
        return False
    otp.verified_at = datetime.utcnow()
    db.session.commit()
    return True

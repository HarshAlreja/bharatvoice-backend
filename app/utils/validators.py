"""Basic input validators used across signup / settings routes."""
import re

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def is_valid_email(email: str) -> bool:
    return bool(email) and bool(EMAIL_RE.match(email))


def is_valid_phone(phone: str) -> bool:
    digits = re.sub(r"\D", "", phone or "")
    return 10 <= len(digits) <= 15

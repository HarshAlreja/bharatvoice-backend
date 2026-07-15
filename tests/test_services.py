"""Unit tests for services that don't need a live Meta/Groq connection."""
from app.utils.validators import is_valid_email, is_valid_phone


def test_email_validator():
    assert is_valid_email("a@b.com")
    assert not is_valid_email("not-an-email")


def test_phone_validator():
    assert is_valid_phone("+919876543210")
    assert not is_valid_phone("123")

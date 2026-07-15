"""Password hashing, token encryption/decryption for per-tenant Meta access tokens."""
import bcrypt
from cryptography.fernet import Fernet
from flask import current_app


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def _fernet():
    key = current_app.config["TOKEN_ENCRYPTION_KEY"]
    return Fernet(key.encode() if isinstance(key, str) else key)


def encrypt_token(plain_token: str) -> str:
    return _fernet().encrypt(plain_token.encode()).decode()


def decrypt_token(encrypted_token: str) -> str:
    return _fernet().decrypt(encrypted_token.encode()).decode()

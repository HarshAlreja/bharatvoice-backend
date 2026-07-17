"""Config classes. get_config() picks Dev/Prod based on FLASK_ENV."""
import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


class BaseConfig:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=7)

    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    SARVAM_API_KEY = os.getenv("SARVAM_API_KEY")

    # Free HuggingFace Inference API token -- used for embeddings instead of
    # loading torch/sentence-transformers locally (avoids OOM on low-RAM hosts).
    # Get one at huggingface.co -> Settings -> Access Tokens -> "Read" token.
    HF_TOKEN = os.getenv("HF_TOKEN")

    # Meta Developer App level (ONE-TIME setup, not per-client)
    META_APP_ID = os.getenv("META_APP_ID")
    META_APP_SECRET = os.getenv("META_APP_SECRET")
    META_API_VERSION = os.getenv("META_API_VERSION", "v21.0")
    META_CONFIGURATION_ID = os.getenv("META_CONFIGURATION_ID")
    META_WEBHOOK_VERIFY_TOKEN = os.getenv("META_WEBHOOK_VERIFY_TOKEN")

    TOKEN_ENCRYPTION_KEY = os.getenv("TOKEN_ENCRYPTION_KEY")

    SMTP_HOST = os.getenv("SMTP_HOST")
    SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
    SMTP_USER = os.getenv("SMTP_USER")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")


class DevConfig(BaseConfig):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///dev.db")


class ProdConfig(BaseConfig):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=2)


def get_config():
    env = os.getenv("FLASK_ENV", "development")
    return ProdConfig if env == "production" else DevConfig
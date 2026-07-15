"""Webhook should never 500 on malformed/non-message payloads (status updates etc)."""
import pytest
from app import create_app
from app.extensions import db


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    with app.app_context():
        db.create_all()
        yield app.test_client()


def test_webhook_ignores_non_message_payload(client):
    resp = client.post("/api/webhook/whatsapp", json={"entry": []})
    assert resp.status_code == 200


def test_webhook_verify_handshake(client):
    resp = client.get("/api/webhook/whatsapp?hub.mode=subscribe&hub.verify_token=wrong&hub.challenge=123")
    assert resp.status_code == 403

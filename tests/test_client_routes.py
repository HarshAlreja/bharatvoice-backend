"""Smoke tests for client (tenant-scoped) routes."""
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


def test_dashboard_requires_auth(client):
    resp = client.get("/api/dashboard/overview")
    assert resp.status_code == 401


def test_signup_requires_all_fields(client):
    resp = client.post("/api/auth/signup", json={"email": "a@a.com"})
    assert resp.status_code == 400

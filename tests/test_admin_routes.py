"""Smoke tests for admin routes. Extend with real fixtures + a test DB."""
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


def test_admin_login_rejects_bad_credentials(client):
    resp = client.post("/api/auth/admin-login", json={"email": "x@x.com", "password": "wrong"})
    assert resp.status_code == 401


def test_businesses_route_requires_auth(client):
    resp = client.get("/api/admin/businesses")
    assert resp.status_code == 401

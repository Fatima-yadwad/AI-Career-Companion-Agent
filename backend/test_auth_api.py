import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.testclient import TestClient

from backend.main import app, create_database


create_database()
client = TestClient(app)


def test_auth_flow_for_two_users():
    # Register first user
    user_a = {
        "full_name": "Alice User",
        "email": "alice.auth@example.com",
        "password": "StrongPass123!",
        "confirm_password": "StrongPass123!"
    }
    res = client.post("/auth/register", json=user_a)
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["user"]["email"] == user_a["email"]
    assert "password_hash" not in str(data)
    token_a = data["token"]
    profile_a = data["profile"]

    # Register second user
    user_b = {
        "full_name": "Bob User",
        "email": "bob.auth@example.com",
        "password": "AnotherPass456!",
        "confirm_password": "AnotherPass456!"
    }
    res = client.post("/auth/register", json=user_b)
    assert res.status_code == 200, res.text
    data_b = res.json()
    token_b = data_b["token"]

    # Login as A
    res = client.post("/auth/login", json={
        "email": user_a["email"],
        "password": user_a["password"]
    })
    assert res.status_code == 200, res.text
    assert res.json()["user"]["email"] == user_a["email"]

    # Token based me endpoint
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token_a}"})
    assert me.status_code == 200, me.text
    assert me.json()["user"]["id"] == profile_a["user_id"]

    # User A profile should not access User B profile
    protected = client.get(f"/profiles/{data_b['profile']['id']}", headers={"Authorization": f"Bearer {token_a}"})
    assert protected.status_code == 403, protected.text

    # Logout returns success
    logout = client.post("/auth/logout", headers={"Authorization": f"Bearer {token_a}"})
    assert logout.status_code == 200, logout.text

    # Token invalid after logout
    me_after = client.get("/auth/me", headers={"Authorization": f"Bearer {token_a}"})
    assert me_after.status_code == 401, me_after.text

    # Login as B and ensure profile data loads
    res_b = client.post("/auth/login", json={
        "email": user_b["email"],
        "password": user_b["password"]
    })
    assert res_b.status_code == 200, res_b.text
    me_b = client.get("/auth/me", headers={"Authorization": f"Bearer {res_b.json()['token']}"})
    assert me_b.status_code == 200, me_b.text
    assert me_b.json()["user"]["email"] == user_b["email"]


def test_auth_validation_errors():
    res = client.post("/auth/register", json={
        "full_name": "",
        "email": "bad-email",
        "password": "short",
        "confirm_password": "different"
    })
    assert res.status_code == 422, res.text

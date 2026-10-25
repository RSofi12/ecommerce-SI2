import uuid
import pytest
from fastapi.testclient import TestClient

try:
    from backend.main import app
except ModuleNotFoundError:
    from main import app

client = TestClient(app)

@pytest.fixture
def auth_header():
    random_id = uuid.uuid4().hex[:8]
    email = f"user_{random_id}@example.com"
    password = "SecurePassword123!"
    
    # Register
    reg_resp = client.post("/api/auth/register", json={
        "email": email,
        "name": "Original Name",
        "password": password,
        "gender": "femenino",
    })
    assert reg_resp.status_code == 201, reg_resp.text
    token = reg_resp.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}", "email": email}

def test_get_profile_me(auth_header):
    resp = client.get("/api/users/me", headers={"Authorization": auth_header["Authorization"]})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["email"] == auth_header["email"]
    assert data["name"] == "Original Name"

def test_update_profile_me(auth_header):
    new_email = f"updated_{uuid.uuid4().hex[:8]}@example.com"
    resp = client.put(
        "/api/users/me",
        headers={"Authorization": auth_header["Authorization"]},
        json={
            "name": "Updated Name",
            "email": new_email,
            "gender": "femenino"
        }
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["name"] == "Updated Name"
    assert data["email"] == new_email

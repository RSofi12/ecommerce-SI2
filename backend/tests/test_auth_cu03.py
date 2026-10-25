# tests for authentication (CU03)

import pytest
from fastapi.testclient import TestClient
try:
    from backend.main import app
except ModuleNotFoundError:
    from main import app

client = TestClient(app)

@pytest.fixture
def test_user():
    import uuid
    random_email = f"testuser_{uuid.uuid4().hex[:8]}@example.com"
    return {
        "email": random_email,
        "name": "Test User",
        "password": "testpassword123",
        "gender": "masculino",
    }

def test_register_and_login(test_user):
    # Register
    response = client.post("/api/auth/register", json={
        "email": test_user["email"],
        "name": test_user["name"],
        "password": test_user["password"],
        "gender": test_user["gender"],
    })
    assert response.status_code == 201, f"Register failed: {response.text}"
    data = response.json()
    assert "access_token" in data["data"]
    # Login
    login_resp = client.post("/api/auth/login", json={
        "email": test_user["email"],
        "password": test_user["password"],
    })
    assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
    login_data = login_resp.json()
    assert "access_token" in login_data["data"]

def test_protected_route_requires_token():
    resp = client.get("/api/users/me")
    assert resp.status_code in (401, 403)

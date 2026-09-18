from fastapi.testclient import TestClient
from app.main import app, hash_password, pwd_context


def test_health():
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_openapi_documents_geojson_and_analytics():
    paths = TestClient(app).get("/openapi.json").json()["paths"]
    assert "/api/sites/geojson" in paths
    assert "/api/sites/{site_id}/analytics" in paths


def test_login_rejects_json_instead_of_form_data():
    response = TestClient(app).post(
        "/api/auth/login", json={"username": "admin@example.com", "password": "password"}
    )
    assert response.status_code == 422


def test_password_hash_is_not_plaintext():
    password = "demo-password-2026"
    hashed = hash_password(password)
    assert hashed != password
    assert pwd_context.verify(password, hashed)


def test_openapi_documents_site_update():
    paths = TestClient(app).get("/openapi.json").json()["paths"]
    assert "/api/sites/{site_id}" in paths
    assert "put" in paths["/api/sites/{site_id}"]

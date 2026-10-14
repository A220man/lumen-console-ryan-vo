import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient


def test_login_redirects_to_oidc(client):
    with patch('app.api.auth.get_oidc_config') as mock_config:
        mock_config.return_value = AsyncMock()
        mock_config.return_value.authorization_endpoint = "http://keycloak:8080/realms/lumen/protocol/openid-connect/auth"
        
        response = client.get("/api/v1/auth/login")
        assert response.status_code == 200
        data = response.json()
        assert "auth_url" in data
        assert "state" in data
        assert "nonce" in data
        assert "code_verifier" in data


def test_logout_clears_cookies(client):
    response = client.post("/api/v1/auth/logout")
    assert response.status_code == 200
    data = response.json()
    assert "logout_url" in data


def test_me_requires_auth(client):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_health_endpoint(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "1.0.0"
    assert "demo_mode" in data
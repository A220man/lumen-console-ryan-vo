import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from uuid import uuid4


def test_list_skills_requires_auth(client):
    response = client.get("/api/v1/skills")
    assert response.status_code == 401


def test_search_skills_requires_auth(client):
    response = client.get("/api/v1/skills/search?q=test")
    assert response.status_code == 401


def test_install_skill_requires_auth(client):
    response = client.post("/api/v1/skills/install", json={
        "source_url": "https://github.com/test/repo",
        "skill_name": "test-skill",
        "scope": "project"
    })
    assert response.status_code == 401


def test_get_lock_file_requires_auth(client):
    response = client.get("/api/v1/lock")
    assert response.status_code == 401


def test_install_from_lock_requires_auth(client):
    response = client.post("/api/v1/lock/install", json={
        "scope": "project",
        "force": False
    })
    assert response.status_code == 401


def test_skill_detail_requires_auth(client):
    response = client.get(f"/api/v1/skills/{uuid4()}")
    assert response.status_code == 401
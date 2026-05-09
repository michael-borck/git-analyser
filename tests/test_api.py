from importlib.metadata import version

import pytest
from fastapi.testclient import TestClient

from git_analyser.api import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": version("git-analyser")}


def test_analyse_valid_repo(temp_repo):
    response = client.post("/analyse", json={"repo": str(temp_repo)})
    assert response.status_code == 200
    data = response.json()
    assert data["commit_count"] >= 2
    assert data["error"] is None


def test_analyse_zip_path_returns_400():
    response = client.post("/analyse", json={"repo": "/some/path/repo.zip"})
    assert response.status_code == 400
    assert "bundle-analyser" in response.json()["detail"]


def test_analyse_nonexistent_path_returns_400():
    response = client.post(
        "/analyse", json={"repo": "/nonexistent/path/that/cannot/exist"}
    )
    assert response.status_code == 400
    detail = response.json()["detail"].lower()
    assert "exist" in detail or "not found" in detail or "git" in detail


def test_analyse_missing_body_returns_422():
    response = client.post("/analyse", json={})
    assert response.status_code == 422


def test_analyse_returns_learning_signals(temp_repo):
    response = client.post("/analyse", json={"repo": str(temp_repo)})
    assert response.status_code == 200
    sig = response.json()["learning_signals"]
    assert sig["commit_count"] == 2
    # Only the second commit's 1 addition counts (root commit has no parent).
    assert sig["total_additions"] == 1
    assert sig["total_deletions"] == 0
    assert sig["add_delete_ratio"] == 0.0
    assert sig["generic_message_ratio"] == 0.0

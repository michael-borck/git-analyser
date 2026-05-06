import pytest
from fastapi.testclient import TestClient

from git_analyser.api import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


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
    response = client.post("/analyse", json={"repo": "/nonexistent/path/repo"})
    assert response.status_code == 400


def test_analyse_missing_body_returns_422():
    response = client.post("/analyse", json={})
    assert response.status_code == 422


def test_analyse_returns_learning_signals(temp_repo):
    response = client.post("/analyse", json={"repo": str(temp_repo)})
    assert response.status_code == 200
    data = response.json()
    sig = data["learning_signals"]
    assert "commit_count" in sig
    assert "total_additions" in sig
    assert "add_delete_ratio" in sig
    assert "commit_regularity_cv" in sig

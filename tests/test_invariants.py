"""Invariant tests — fast, run by default."""

from importlib.metadata import version

import pytest


def test_package_imports_cleanly() -> None:
    """Smoke alarm — package must import without errors."""
    import git_analyser  # noqa: F401
    from git_analyser.cli import main  # noqa: F401
    from git_analyser.api import app  # noqa: F401


def test_health_version_matches_installed_package() -> None:
    """/health must report the actual installed package version."""
    from fastapi.testclient import TestClient

    from git_analyser.api import app

    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["version"] == version("git-analyser")


def test_app_title_matches_installed_package() -> None:
    """FastAPI app.version must match the installed package."""
    from git_analyser.api import app

    assert app.version == version("git-analyser")


def test_non_git_directory_returns_loud_error(tmp_path) -> None:
    """A directory without .git must error explicitly, not silently zero-fill.

    Family pattern: failures are loud, not silent.
    """
    from git_analyser.core import analyse_repo

    result = analyse_repo(tmp_path)
    assert result.error is not None
    # Must NOT have populated signals — silent zero-fill is a real risk
    assert result.commit_count == 0
    assert result.suspicious_flags == []
    assert result.learning_signals.commit_count == 0

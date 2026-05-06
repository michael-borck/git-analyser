import subprocess
from pathlib import Path

import pytest


@pytest.fixture
def temp_repo(tmp_path):
    """Create a minimal git repo for testing."""
    subprocess.run(["git", "init", str(tmp_path)], check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    # First commit
    (tmp_path / "index.html").write_text("<html></html>")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "add index.html"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    # Second commit
    (tmp_path / "style.css").write_text("body { margin: 0; }")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "add stylesheet"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    return tmp_path

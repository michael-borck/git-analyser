from pathlib import Path

import pytest

from git_analyser.core import analyse_repo
from git_analyser.models import GitAnalysisResult


def test_valid_repo_returns_result(temp_repo):
    result = analyse_repo(temp_repo)
    assert isinstance(result, GitAnalysisResult)
    assert result.error is None
    assert result.commit_count >= 2


def test_valid_repo_has_authors(temp_repo):
    result = analyse_repo(temp_repo)
    assert len(result.authors) >= 1
    assert "Test" in result.authors


def test_valid_repo_has_timeline(temp_repo):
    result = analyse_repo(temp_repo)
    assert len(result.timeline) >= 2
    # First commit subject
    subjects = [c.subject for c in result.timeline]
    assert "add index.html" in subjects


def test_zip_path_returns_bundle_analyser_error():
    result = analyse_repo("/some/path/repo.zip")
    assert result.error is not None
    assert "bundle-analyser" in result.error


def test_nonexistent_path_returns_error():
    result = analyse_repo("/nonexistent/path/to/repo")
    assert result.error is not None
    assert result.commit_count == 0


def test_path_without_git_returns_error(tmp_path):
    result = analyse_repo(tmp_path)
    assert result.error is not None
    assert ".git" in result.error or "not a git" in result.error


def test_learning_signals_values_are_deterministic(temp_repo):
    """The 2-commit fixture has known signal values; pin them.

    Note: the first (root) commit has no parent so diff-tree --numstat
    reports nothing for it, hence only the second commit's 1 addition is
    counted. This matches the current implementation's behaviour.
    """
    result = analyse_repo(temp_repo)
    sig = result.learning_signals
    assert sig.commit_count == 2
    assert sig.total_additions == 1  # only the second commit's line is counted
    assert sig.total_deletions == 0
    assert sig.add_delete_ratio == 0.0
    assert sig.generic_message_ratio == 0.0  # both messages are descriptive
    # avg_message_length: "add index.html" (14) + "add stylesheet" (14) / 2 = 14
    assert sig.avg_message_length == 14.0


def test_string_path_accepted(temp_repo):
    result = analyse_repo(str(temp_repo))
    assert result.error is None
    assert result.commit_count >= 2


def test_remote_url_invokes_git_clone(monkeypatch):
    """Remote URLs trigger git clone with the right argv (no network)."""
    import subprocess as _subprocess
    from pathlib import Path as _Path
    from unittest.mock import MagicMock

    from git_analyser import core as _core

    captured_calls: list[list[str]] = []
    real_run = _subprocess.run

    def fake_run(cmd, *args, **kwargs):
        captured_calls.append(list(cmd))
        if isinstance(cmd, list) and len(cmd) >= 2 and cmd[0] == "git" and cmd[1] == "clone":
            target = cmd[-1]
            target_path = _Path(target)
            target_path.mkdir(parents=True, exist_ok=True)
            (target_path / ".git").mkdir(exist_ok=True)
            mock = MagicMock()
            mock.returncode = 0
            mock.stdout = ""
            mock.stderr = ""
            return mock
        # All other git invocations (log, diff-tree...) — return empty output
        mock = MagicMock()
        mock.returncode = 0
        mock.stdout = ""
        mock.stderr = ""
        return mock

    # Patch the symbol used inside core.py
    monkeypatch.setattr(_core.subprocess, "run", fake_run)

    result = analyse_repo("https://github.com/example/repo.git")

    clone_calls = [
        c for c in captured_calls
        if len(c) >= 2 and c[0] == "git" and c[1] == "clone"
    ]
    assert len(clone_calls) == 1
    assert "https://github.com/example/repo.git" in clone_calls[0]
    # Sanity: result is a GitAnalysisResult, no clone error surfaced
    assert isinstance(result, GitAnalysisResult)
    assert result.error is None or "clone" not in result.error.lower()

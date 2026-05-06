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


def test_learning_signals_has_expected_fields(temp_repo):
    result = analyse_repo(temp_repo)
    sig = result.learning_signals
    assert hasattr(sig, "commit_count")
    assert hasattr(sig, "total_additions")
    assert hasattr(sig, "total_deletions")
    assert hasattr(sig, "add_delete_ratio")
    assert hasattr(sig, "avg_message_length")
    assert hasattr(sig, "generic_message_ratio")
    assert hasattr(sig, "time_span_hours")
    assert hasattr(sig, "max_gap_hours")
    assert hasattr(sig, "commit_regularity_cv")


def test_learning_signals_values(temp_repo):
    result = analyse_repo(temp_repo)
    sig = result.learning_signals
    assert sig.commit_count >= 2
    assert sig.total_additions >= 0
    assert sig.avg_message_length > 0


def test_string_path_accepted(temp_repo):
    result = analyse_repo(str(temp_repo))
    assert result.error is None
    assert result.commit_count >= 2

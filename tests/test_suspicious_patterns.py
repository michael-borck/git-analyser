"""POS/NEG matrix for the four suspicious-pattern rules in core.py.

Each of the four rules (bulk upload, single-session 24h dump, massive
commit, multi-author) gets one positive and one negative test using
deterministic fixtures with forged commit dates and author emails.
"""
from __future__ import annotations

import os
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from git_analyser.core import analyse_repo


def _git_init(repo: Path) -> None:
    subprocess.run(["git", "init", str(repo)], check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=repo,
        check=True,
        capture_output=True,
    )


def _commit(
    repo: Path,
    message: str,
    when: datetime,
    author_name: str = "Test",
    author_email: str = "test@test.com",
) -> None:
    """Create a commit with forged author/committer dates and identity."""
    iso = when.isoformat()
    env = {
        **os.environ,
        "GIT_AUTHOR_DATE": iso,
        "GIT_COMMITTER_DATE": iso,
        "GIT_AUTHOR_NAME": author_name,
        "GIT_AUTHOR_EMAIL": author_email,
        "GIT_COMMITTER_NAME": author_name,
        "GIT_COMMITTER_EMAIL": author_email,
    }
    subprocess.run(
        ["git", "add", "."], cwd=repo, check=True, capture_output=True, env=env
    )
    subprocess.run(
        ["git", "commit", "-m", message],
        cwd=repo,
        check=True,
        capture_output=True,
        env=env,
    )


def _make_repo(tmp_path: Path, num_commits: int, span_hours: float) -> Path:
    """Init repo, make N commits spread evenly over span_hours."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _git_init(repo)

    start = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    step = timedelta(hours=span_hours / max(num_commits - 1, 1))

    for i in range(num_commits):
        (repo / f"file_{i}.txt").write_text(f"content {i}\n")
        when = start + step * i
        _commit(repo, f"add file_{i}", when)

    return repo


def _make_repo_with_huge_commit(tmp_path: Path, lines: int) -> Path:
    """Init repo, make a baseline commit, then a huge commit with N lines added."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _git_init(repo)

    start = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

    # Baseline commit (the root commit's diff doesn't show in numstat)
    (repo / "seed.txt").write_text("seed\n")
    _commit(repo, "seed file", start)

    # Huge commit on top
    huge = "\n".join(f"line {i}" for i in range(lines)) + "\n"
    (repo / "huge.txt").write_text(huge)
    _commit(repo, "add huge file", start + timedelta(hours=1))

    return repo


def _make_repo_with_multiple_authors(tmp_path: Path, num_authors: int) -> Path:
    """Init repo with one commit per author (distinct emails)."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _git_init(repo)

    start = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

    for i in range(num_authors):
        (repo / f"file_{i}.txt").write_text(f"content {i}\n")
        when = start + timedelta(hours=i * 10)
        _commit(
            repo,
            f"add file_{i}",
            when,
            author_name=f"Author{i}",
            author_email=f"author{i}@example.com",
        )

    return repo


# ---- bulk-upload rule (`<= 2 commits`) -------------------------------------


def test_no_bulk_upload_flag_for_more_than_two_commits(tmp_path):
    """3+ commits should NOT trigger the bulk-upload flag."""
    repo = _make_repo(tmp_path, num_commits=4, span_hours=72)
    result = analyse_repo(repo)
    assert not any("bulk upload" in flag.lower() for flag in result.suspicious_flags)


# ---- 24-hour-dump rule -----------------------------------------------------


def test_no_24h_dump_flag_when_span_exceeds_day(tmp_path):
    """Commits spanning >24h should NOT trigger the single-session-dump flag."""
    repo = _make_repo(tmp_path, num_commits=4, span_hours=72)
    result = analyse_repo(repo)
    assert not any(
        "single session" in flag.lower() for flag in result.suspicious_flags
    )


# ---- massive-commit rule (>500 additions) ----------------------------------


def test_massive_commit_flagged(tmp_path):
    """A commit with >500 additions triggers the very-large-commit flag."""
    repo = _make_repo_with_huge_commit(tmp_path, lines=600)
    result = analyse_repo(repo)
    assert any(
        "addition" in flag.lower() or "large" in flag.lower()
        for flag in result.suspicious_flags
    )


def test_no_massive_commit_flag_for_small_commits(tmp_path):
    """Small commits don't trigger the very-large-commit flag."""
    repo = _make_repo(tmp_path, num_commits=3, span_hours=48)
    result = analyse_repo(repo)
    assert not any(
        "addition" in flag.lower() and "large" in flag.lower()
        for flag in result.suspicious_flags
    )


# ---- multi-author rule (`> 2` distinct emails) -----------------------------


def test_multi_author_flagged(tmp_path):
    """3+ distinct author emails triggers the multi-author flag."""
    repo = _make_repo_with_multiple_authors(tmp_path, num_authors=3)
    result = analyse_repo(repo)
    assert any(
        "author" in flag.lower() and "multiple" in flag.lower()
        for flag in result.suspicious_flags
    )


def test_no_multi_author_flag_for_single_author(tmp_path):
    """Single author should NOT trigger the multi-author flag."""
    repo = _make_repo(tmp_path, num_commits=4, span_hours=48)
    result = analyse_repo(repo)
    assert not any(
        "author" in flag.lower() and "multiple" in flag.lower()
        for flag in result.suspicious_flags
    )

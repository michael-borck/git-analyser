"""
Analyse git history of a repository.

Signals captured:
- Commit count, timeline, frequency
- Commit size distribution (additions/deletions per commit)
- Author consistency
- Message quality (length, descriptiveness)
- Time span (first to last commit)
- Large file additions
- Evidence of learning: iteration patterns, add/delete ratio
"""
import shutil
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path

from .models import CommitSummary, GitAnalysisResult, LearningSignals


def run_git(repo_dir: Path, args: list[str]) -> str:
    """Run a git command in the repo directory."""
    result = subprocess.run(
        ["git"] + args,
        cwd=repo_dir,
        capture_output=True,
        text=True,
        timeout=30,
    )
    return result.stdout.strip()


def get_commits(repo_dir: Path) -> list[dict]:
    """Get all commits with metadata."""
    # Format: hash|author_name|author_email|date|subject
    log = run_git(repo_dir, [
        "log", "--all", "--format=%H|%an|%ae|%aI|%s", "--reverse"
    ])
    if not log:
        return []

    commits = []
    for line in log.splitlines():
        parts = line.split("|", 4)
        if len(parts) < 5:
            continue
        commits.append({
            "hash": parts[0],
            "author_name": parts[1],
            "author_email": parts[2],
            "date": parts[3],
            "subject": parts[4],
        })
    return commits


def get_commit_stats(repo_dir: Path, commit_hash: str) -> dict:
    """Get file change stats for a commit."""
    # --numstat gives: additions\tdeletions\tfilename
    numstat = run_git(repo_dir, [
        "diff-tree", "--no-commit-id", "--numstat", "-r", commit_hash
    ])
    files = []
    total_add = 0
    total_del = 0
    for line in numstat.splitlines():
        parts = line.split("\t", 2)
        if len(parts) == 3:
            add = int(parts[0]) if parts[0] != "-" else 0
            delete = int(parts[1]) if parts[1] != "-" else 0
            files.append({"file": parts[2], "additions": add, "deletions": delete})
            total_add += add
            total_del += delete
    return {"files": files, "total_additions": total_add, "total_deletions": total_del, "file_count": len(files)}


def detect_suspicious_patterns(commits: list[dict]) -> list[str]:
    """Flag potentially suspicious patterns."""
    flags = []

    if len(commits) <= 2:
        flags.append(f"Very few commits ({len(commits)}) — possible bulk upload")

    if len(commits) >= 2:
        first = datetime.fromisoformat(commits[0]["date"])
        last = datetime.fromisoformat(commits[-1]["date"])
        span_hours = (last - first).total_seconds() / 3600
        if span_hours < 24:
            flags.append(
                f"All commits within {span_hours:.1f} hours — possible single session dump"
            )

    # Check for massive commits
    for commit in commits:
        if commit.get("total_additions", 0) > 500:
            flags.append(
                f"Commit {commit['hash'][:8]} has {commit['total_additions']} additions — very large commit"
            )

    # Check author consistency
    authors = set(c["author_email"] for c in commits)
    if len(authors) > 2:
        flags.append(f"Multiple authors detected: {authors}")

    return flags


def compute_learning_signals(commits: list[dict]) -> LearningSignals:
    """Compute signals that suggest evidence of learning/iteration."""
    if not commits:
        return LearningSignals(
            commit_count=0,
            total_additions=0,
            total_deletions=0,
            add_delete_ratio=0.0,
            avg_message_length=0.0,
            generic_message_ratio=0.0,
            time_span_hours=0.0,
            max_gap_hours=0.0,
            commit_regularity_cv=0.0,
        )

    total_add = sum(c.get("total_additions", 0) for c in commits)
    total_del = sum(c.get("total_deletions", 0) for c in commits)

    add_del_ratio = total_del / max(total_add, 1)

    msg_lengths = [len(c["subject"]) for c in commits]
    avg_msg_len = sum(msg_lengths) / len(msg_lengths)

    generic_messages = sum(
        1
        for c in commits
        if c["subject"].lower()
        in (
            "update",
            "fix",
            "changes",
            ".",
            "commit",
            "initial commit",
            "first commit",
            "added files",
            "upload",
            "updated",
        )
    )
    generic_ratio = generic_messages / len(commits)

    total_span = 0.0
    max_gap = 0.0
    gap_cv = 0.0

    if len(commits) >= 2:
        dates = [datetime.fromisoformat(c["date"]) for c in commits]
        total_span = (dates[-1] - dates[0]).total_seconds()
        if total_span > 0 and len(dates) > 2:
            gaps = [
                (dates[i + 1] - dates[i]).total_seconds()
                for i in range(len(dates) - 1)
            ]
            avg_gap = sum(gaps) / len(gaps)
            max_gap = max(gaps)
            gap_cv = (
                (sum((g - avg_gap) ** 2 for g in gaps) / len(gaps)) ** 0.5
                / max(avg_gap, 1)
            )
        else:
            max_gap = total_span

    return LearningSignals(
        commit_count=len(commits),
        total_additions=total_add,
        total_deletions=total_del,
        add_delete_ratio=round(add_del_ratio, 2),
        avg_message_length=round(avg_msg_len, 1),
        generic_message_ratio=round(generic_ratio, 2),
        time_span_hours=round(total_span / 3600, 1) if total_span else 0.0,
        max_gap_hours=round(max_gap / 3600, 1) if max_gap else 0.0,
        commit_regularity_cv=round(gap_cv, 2),
    )


def _analyse_local(repo_path: Path) -> GitAnalysisResult:
    """Run analysis on a local git repository path."""
    # Validate git repo
    if not repo_path.exists():
        return GitAnalysisResult(
            repo=str(repo_path),
            commit_count=0,
            authors=[],
            timeline=[],
            suspicious_flags=[],
            learning_signals=LearningSignals(
                commit_count=0,
                total_additions=0,
                total_deletions=0,
                add_delete_ratio=0.0,
                avg_message_length=0.0,
                generic_message_ratio=0.0,
                time_span_hours=0.0,
                max_gap_hours=0.0,
                commit_regularity_cv=0.0,
            ),
            error=f"Path does not exist: {repo_path}",
        )

    if not (repo_path / ".git").exists():
        return GitAnalysisResult(
            repo=str(repo_path),
            commit_count=0,
            authors=[],
            timeline=[],
            suspicious_flags=[],
            learning_signals=LearningSignals(
                commit_count=0,
                total_additions=0,
                total_deletions=0,
                add_delete_ratio=0.0,
                avg_message_length=0.0,
                generic_message_ratio=0.0,
                time_span_hours=0.0,
                max_gap_hours=0.0,
                commit_regularity_cv=0.0,
            ),
            error=f"No .git directory found at {repo_path} — not a git repository",
        )

    commits = get_commits(repo_path)

    # Enrich commits with stats
    for commit in commits:
        stats = get_commit_stats(repo_path, commit["hash"])
        commit["total_additions"] = stats["total_additions"]
        commit["total_deletions"] = stats["total_deletions"]
        commit["file_count"] = stats["file_count"]

    # Build timeline
    timeline = [
        CommitSummary(
            hash=c["hash"],
            date=c["date"],
            subject=c["subject"],
            additions=c.get("total_additions", 0),
            deletions=c.get("total_deletions", 0),
            file_count=c.get("file_count", 0),
        )
        for c in commits
    ]

    authors = sorted(set(c["author_name"] for c in commits))
    suspicious_flags = detect_suspicious_patterns(commits)
    learning_signals = compute_learning_signals(commits)

    return GitAnalysisResult(
        repo=str(repo_path),
        commit_count=len(commits),
        authors=authors,
        timeline=timeline,
        suspicious_flags=suspicious_flags,
        learning_signals=learning_signals,
    )


def _empty_error_result(repo: str, error: str) -> GitAnalysisResult:
    """Return an error GitAnalysisResult with zero-valued signals."""
    return GitAnalysisResult(
        repo=repo,
        commit_count=0,
        authors=[],
        timeline=[],
        suspicious_flags=[],
        learning_signals=LearningSignals(
            commit_count=0,
            total_additions=0,
            total_deletions=0,
            add_delete_ratio=0.0,
            avg_message_length=0.0,
            generic_message_ratio=0.0,
            time_span_hours=0.0,
            max_gap_hours=0.0,
            commit_regularity_cv=0.0,
        ),
        error=error,
    )


def analyse_repo(repo: str | Path) -> GitAnalysisResult:
    """
    Analyse a git repository and return learning signals.

    Accepts:
    - Local path (str or Path)
    - Remote URL (http://, https://, git@) — cloned to a temp dir
    - Zip files — rejected with a helpful message
    """
    repo_str = str(repo)

    # Reject zip files
    if repo_str.endswith(".zip"):
        return _empty_error_result(
            repo_str,
            "No git history in a zip file. To analyse file contents, use bundle-analyser.",
        )

    # Remote URL — clone to temp dir
    is_remote = (
        repo_str.startswith("http://")
        or repo_str.startswith("https://")
        or repo_str.startswith("git@")
    )

    if is_remote:
        tmp_dir = tempfile.mkdtemp()
        try:
            result = subprocess.run(
                ["git", "clone", repo_str, tmp_dir],
                capture_output=True,
                text=True,
                timeout=120,
            )
            if result.returncode != 0:
                return _empty_error_result(
                    repo_str,
                    f"Failed to clone repository: {result.stderr.strip()}",
                )
            return _analyse_local(Path(tmp_dir))
        except subprocess.TimeoutExpired:
            return _empty_error_result(repo_str, "Clone timed out after 120 seconds")
        except Exception as exc:
            return _empty_error_result(repo_str, f"Clone error: {exc}")
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    # Local path
    return _analyse_local(Path(repo_str))

from importlib.metadata import version as _v
from pathlib import Path

from .core import analyse_repo
from .manifest import MANIFEST
from .models import GitAnalysisResult

__version__ = _v("git-analyser")
del _v

# Canonical alias for the family's uniform public surface.
GitAnalysis = GitAnalysisResult


class GitAnalyser:
    """Thin facade over :func:`analyse_repo` for the family's canonical call shape."""

    def analyse(self, repo: str | Path) -> GitAnalysisResult:
        return analyse_repo(repo)


def analyse(repo: str | Path) -> GitAnalysisResult:
    """Module-level convenience wrapper around :func:`analyse_repo`."""
    return analyse_repo(repo)


__all__ = [
    "GitAnalyser",
    "GitAnalysis",
    "GitAnalysisResult",
    "analyse",
    "MANIFEST",
    "__version__",
]

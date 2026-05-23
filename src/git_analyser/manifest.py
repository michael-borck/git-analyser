"""Capability manifest for the lens family (consumed by auto-analyser).

git-analyser is invoked on a repository path/zip rather than a file extension, so
it claims no extensions for auto-routing (auto-analyser reaches it explicitly).
"""
from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version


def _version() -> str:
    try:
        return version("git-analyser")
    except PackageNotFoundError:
        return "0.0.0"


MANIFEST: dict = {
    "name": "git-analyser",
    "version": _version(),
    "role": "analyser",
    "accepts": ["git-repo"],
    "extensions": [],
    "auto_routable": False,
    "produces": "GitAnalysisResult",
}

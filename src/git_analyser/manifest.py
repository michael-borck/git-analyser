"""Capability manifest for the lens family (consumed by auto-analyser).

git-analyser is invoked on a repository path/zip rather than a file extension, so
it claims no extensions for auto-routing (auto-analyser reaches it explicitly).
"""
from __future__ import annotations

from lens_contract import make_manifest

MANIFEST = make_manifest(
    name="git-analyser",
    accepts=["git-repo"],
    extensions=[],
    auto_routable=False,
    produces="GitAnalysisResult",
)

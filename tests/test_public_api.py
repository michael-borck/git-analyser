"""Tests for the canonical public API surface."""
import git_analyser
from git_analyser import (
    MANIFEST,
    GitAnalyser,
    GitAnalysis,
    GitAnalysisResult,
    __version__,
    analyse,
)


def test_canonical_names_import():
    assert GitAnalyser is not None
    assert GitAnalysis is not None
    assert GitAnalysisResult is not None
    assert MANIFEST is not None


def test_gitanalysis_is_alias():
    assert GitAnalysis is GitAnalysisResult


def test_analyse_callable():
    assert callable(analyse)


def test_facade_has_analyse():
    assert callable(GitAnalyser().analyse)


def test_manifest_name():
    assert MANIFEST["name"] == "git-analyser"


def test_version_is_str():
    assert isinstance(__version__, str)


def test_all_lists_canonical_names():
    for name in (
        "GitAnalyser",
        "GitAnalysis",
        "GitAnalysisResult",
        "analyse",
        "MANIFEST",
        "__version__",
    ):
        assert name in git_analyser.__all__

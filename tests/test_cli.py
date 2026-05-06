import json
import subprocess
import sys
from pathlib import Path

# Resolve the venv python for the project so subprocess calls find git_analyser
_PROJECT_ROOT = Path(__file__).parent.parent
_VENV_PYTHON = _PROJECT_ROOT / ".venv" / "bin" / "python"

# Fall back to sys.executable when running inside the venv already
_PYTHON = str(_VENV_PYTHON) if _VENV_PYTHON.exists() else sys.executable


def test_help_exits_zero():
    result = subprocess.run(
        [_PYTHON, "-m", "git_analyser.cli", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "git-analyser" in result.stdout


def test_serve_help_exits_zero():
    result = subprocess.run(
        [_PYTHON, "-m", "git_analyser.cli", "serve", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "serve" in result.stdout


def test_no_args_exits_nonzero():
    result = subprocess.run(
        [_PYTHON, "-m", "git_analyser.cli"],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0


def test_json_output(temp_repo):
    result = subprocess.run(
        [_PYTHON, "-m", "git_analyser.cli", str(temp_repo), "--json"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["commit_count"] >= 2
    assert "learning_signals" in data

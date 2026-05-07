from __future__ import annotations

from importlib.metadata import version as _pkg_version

import argparse
import json
import sys

import uvicorn
from rich.console import Console
from rich.table import Table

from .core import analyse_repo

console = Console()


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="git-analyser",
        description="Analyse git repository history and commit patterns",
    )
    parser.add_argument("--version", action="version", version=_pkg_version("git-analyser"))

    sub = parser.add_subparsers(dest="command")

    # serve subcommand
    serve = sub.add_parser("serve", help="Start the HTTP API server")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8007)

    # analyse subcommand (also the default when no subcommand is given)
    analyse = sub.add_parser("analyse", help="Analyse a git repository (default)")
    analyse.add_argument(
        "repo",
        help="Local path or remote URL to git repository",
    )
    analyse.add_argument("--json", action="store_true", help="Output as JSON")

    return parser


def main() -> None:
    # Support the short form: git-analyser <repo> [--json]
    # by detecting whether the first non-flag arg looks like a subcommand.
    argv = sys.argv[1:]

    # If first positional arg is not a known subcommand, inject "analyse"
    known_commands = {"serve", "analyse", "--help", "-h", "--version"}
    if argv and not argv[0].startswith("-") and argv[0] not in {"serve", "analyse"}:
        argv = ["analyse"] + argv

    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "serve":
        uvicorn.run(
            "git_analyser.api:app",
            host=args.host,
            port=args.port,
        )
        return

    if args.command == "analyse":
        result = analyse_repo(args.repo)

        if args.json:
            print(json.dumps(result.model_dump(), indent=2))
            return

        if result.error:
            console.print(f"[red]Error:[/red] {result.error}")
            sys.exit(1)

        _display_result(result)
        return

    # No command given — print help
    parser.print_help()
    sys.exit(1)


def _display_result(result) -> None:
    """Render analysis results with Rich tables."""
    sig = result.learning_signals

    console.print(f"\n[bold]Git Analysis:[/bold] {result.repo}")
    console.print(f"Commits: {result.commit_count}  Authors: {len(result.authors)}")
    if result.authors:
        console.print(f"Author(s): {', '.join(result.authors)}")

    # Signals table
    table = Table(title="Learning Signals", show_header=True, header_style="bold cyan")
    table.add_column("Signal", style="dim")
    table.add_column("Value")

    table.add_row("Time span (hours)", str(sig.time_span_hours))
    table.add_row("Total additions", str(sig.total_additions))
    table.add_row("Total deletions", str(sig.total_deletions))
    table.add_row("Add/delete ratio", str(sig.add_delete_ratio))
    table.add_row("Avg message length", str(sig.avg_message_length))
    table.add_row("Generic message ratio", str(sig.generic_message_ratio))
    table.add_row("Max gap (hours)", str(sig.max_gap_hours))
    table.add_row("Commit regularity CV", str(sig.commit_regularity_cv))

    console.print(table)

    # Suspicious flags
    if result.suspicious_flags:
        console.print("\n[bold yellow]Suspicious Flags:[/bold yellow]")
        for flag in result.suspicious_flags:
            console.print(f"  [yellow]•[/yellow] {flag}")
    else:
        console.print("\n[green]No suspicious patterns detected.[/green]")

    # Recent commits
    if result.timeline:
        recent = Table(
            title="Recent Commits", show_header=True, header_style="bold cyan"
        )
        recent.add_column("Hash", style="dim", width=10)
        recent.add_column("Date", width=20)
        recent.add_column("Subject")
        recent.add_column("+", justify="right", width=6)
        recent.add_column("-", justify="right", width=6)

        for commit in result.timeline[-10:]:
            recent.add_row(
                commit.hash[:8],
                commit.date[:19],
                commit.subject,
                str(commit.additions),
                str(commit.deletions),
            )
        console.print(recent)


if __name__ == "__main__":
    main()

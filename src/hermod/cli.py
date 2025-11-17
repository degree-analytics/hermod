"""Hermod CLI - AI usage collection tool."""

import json
import logging
import os
import re
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from hermod.__version__ import __version__
from hermod.collector import (
    DEFAULT_COMMAND_TIMEOUT_SECONDS,
    MAX_COMMAND_TIMEOUT_SECONDS,
    MIN_COMMAND_TIMEOUT_SECONDS,
    collect_usage,
    save_submission,
)
from hermod.dependencies import check_all_dependencies
from hermod.git_detector import detect_developer
from hermod.logging_config import setup_logging

# Initialize logging
log_level = os.getenv("HERMOD_LOG_LEVEL", "WARNING")
log_file = os.getenv("HERMOD_LOG_FILE")
setup_logging(level=log_level, log_file=Path(log_file) if log_file else None)

logger = logging.getLogger(__name__)

app = typer.Typer(
    name="hermod",
    help="AI usage collection tool for developers",
    no_args_is_help=True,
)
console = Console()

# Input validation constants
DEVELOPER_NAME_MIN_LENGTH = 1
DEVELOPER_NAME_MAX_LENGTH = 100
DAYS_MIN = 1
DAYS_MAX = 365

# Input validation patterns
DEVELOPER_NAME_PATTERN = re.compile(
    rf"^[a-zA-Z0-9\s_-]{{{DEVELOPER_NAME_MIN_LENGTH},{DEVELOPER_NAME_MAX_LENGTH}}}$"
)


def version_callback(value: bool):
    """Show version and exit."""
    if value:
        console.print(f"Hermod version: {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        help="Show version and exit",
        callback=version_callback,
        is_eager=True,
    ),
):
    """Hermod - AI usage collection tool."""
    pass


@app.command()
def collect(
    developer: Optional[str] = typer.Option(
        None,
        "--developer",
        "-d",
        help="Developer canonical name (auto-detected from git if not provided)",
    ),
    days: int = typer.Option(
        7,
        "--days",
        "-n",
        help="Number of days to collect usage data for",
        min=DAYS_MIN,
        max=DAYS_MAX,
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output results as JSON",
    ),
    command_timeout_seconds: Optional[int] = typer.Option(
        None,
        "--timeout",
        "-t",
        min=MIN_COMMAND_TIMEOUT_SECONDS,
        max=MAX_COMMAND_TIMEOUT_SECONDS,
        help=(
            "Max seconds to wait for each ccusage command "
            f"(default {DEFAULT_COMMAND_TIMEOUT_SECONDS}s, "
            f"range {MIN_COMMAND_TIMEOUT_SECONDS}-{MAX_COMMAND_TIMEOUT_SECONDS})."
        ),
    ),
):
    """Collect AI usage data from ccusage and ccusage-codex."""
    # Validate developer name if provided
    if developer is not None:
        if not DEVELOPER_NAME_PATTERN.match(developer):
            error_msg = (
                f"Invalid developer name. Must be {DEVELOPER_NAME_MIN_LENGTH}-{DEVELOPER_NAME_MAX_LENGTH} "
                "characters and contain only letters, numbers, spaces, underscores, and hyphens."
            )
            if json_output:
                console.print(json.dumps({"error": error_msg}))
            else:
                console.print(f"[red]Error:[/red] {error_msg}")
            raise typer.Exit(code=1)

    # Check dependencies
    deps = check_all_dependencies()
    if not all(deps.values()):
        missing = [tool for tool, installed in deps.items() if not installed]
        if json_output:
            console.print(
                json.dumps({"error": f"Dependencies not installed: {', '.join(missing)}"})
            )
        else:
            console.print("[red]Error:[/red] The following dependencies are not installed:")
            for tool in missing:
                console.print(f"  - {tool}")
            console.print("\n[yellow]Installation instructions:[/yellow]")
            console.print("  npm install -g ccusage")
            console.print("  npm install -g @ccusage/codex")
            console.print("\n[blue]📖 Full documentation:[/blue] docs/hermod-installation.md")
        raise typer.Exit(code=1)

    # Detect or use provided developer
    if developer is None:
        try:
            developer = detect_developer()
        except Exception as e:
            if json_output:
                console.print(json.dumps({"error": f"Failed to detect developer: {e}"}))
            else:
                console.print(f"[red]Error:[/red] Failed to detect developer: {e}")
            raise typer.Exit(code=1)

        # Validate auto-detected name as well
        if not DEVELOPER_NAME_PATTERN.match(developer):
            error_msg = (
                f"Auto-detected developer name '{developer}' is invalid. "
                "Please provide a valid name with --developer option."
            )
            if json_output:
                console.print(json.dumps({"error": error_msg}))
            else:
                console.print(f"[red]Error:[/red] {error_msg}")
            raise typer.Exit(code=1)

    # Collect usage data
    if not json_output:
        console.print(f"[blue]Collecting AI usage data for {developer}...[/blue]")

    try:
        data = collect_usage(
            developer,
            days,
            command_timeout_seconds=command_timeout_seconds,
        )
    except Exception as e:
        if json_output:
            console.print(json.dumps({"error": f"Failed to collect usage data: {e}"}))
        else:
            console.print(f"[red]Error:[/red] Failed to collect usage data: {e}")
        raise typer.Exit(code=1)

    # Save submission
    try:
        output_file = save_submission(data, developer)
    except Exception as e:
        if json_output:
            console.print(json.dumps({"error": f"Failed to save submission: {e}"}))
        else:
            console.print(f"[red]Error:[/red] Failed to save submission: {e}")
        raise typer.Exit(code=1)

    # Output results
    if json_output:
        output_data = {
            "developer": developer,
            "days": days,
            "output_file": str(output_file),
            "timeout_seconds": command_timeout_seconds,
            "claude_code": data.get("claude_code", {}),
            "codex": data.get("codex", {}),
        }
        console.print(json.dumps(output_data, indent=2))
    else:
        console.print(f"[green]✓[/green] Successfully collected usage data for {developer}")
        console.print(
            f"[blue]Date range:[/blue] {data['metadata']['date_range']['start']} to {data['metadata']['date_range']['end']}"
        )
        console.print(f"[blue]Output file:[/blue] {output_file}")
        if command_timeout_seconds:
            console.print(f"[blue]Command timeout override:[/blue] {command_timeout_seconds}s")
        elif os.getenv("HERMOD_COMMAND_TIMEOUT_SECONDS"):
            console.print(
                f"[blue]Command timeout source:[/blue] HERMOD_COMMAND_TIMEOUT_SECONDS="
                f"{os.getenv('HERMOD_COMMAND_TIMEOUT_SECONDS')}"
            )

        # Show summary table
        table = Table(title="Usage Summary")
        table.add_column("Tool", style="cyan")
        table.add_column("Total Cost", style="green")

        claude_total = data.get("claude_code", {}).get("totals", {}).get("totalCost", 0)
        codex_totals = data.get("codex", {}).get("totals") or {}
        codex_total = codex_totals.get("totalCost")
        if codex_total is None:
            codex_total = codex_totals.get("costUSD", 0)

        table.add_row("Claude Code", f"${claude_total:.2f}" if claude_total else "N/A")
        table.add_row("Codex", f"${codex_total:.2f}" if codex_total else "N/A")
        table.add_row("Total", f"${claude_total + codex_total:.2f}", style="bold")

        console.print(table)


if __name__ == "__main__":
    app()

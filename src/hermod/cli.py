"""Hermod CLI - AI usage collection tool."""

import json
import logging
import os
import re
import subprocess  # nosec B404 - Legitimate CLI integration with validation
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


@app.command()
def submit(
    submission_dir: Optional[Path] = typer.Option(
        None,
        "--submission-dir",
        help="Directory containing submission files (default: data/ai_usage/submissions)",
    ),
):
    """Submit AI usage data to GitHub Actions workflow.

    This command:
    1. Checks that gh CLI is installed and authenticated
    2. Finds the most recent submission file
    3. Base64 encodes the submission data
    4. Triggers the ai-usage-ingestion GitHub Actions workflow
    5. Cleans up the submission file after successful submission
    """
    import base64
    import shutil

    # Use default submission directory if not provided
    if submission_dir is None:
        submission_dir = Path("data/ai_usage/submissions")

    # Check prerequisites
    console.print("[blue]🔍 Checking prerequisites...[/blue]")

    # Check gh CLI is installed
    if shutil.which("gh") is None:
        console.print("[red]❌ GitHub CLI (gh) is not installed[/red]")
        console.print("   Install with: brew install gh")
        raise typer.Exit(code=1)

    # Check gh is authenticated
    try:
        result = subprocess.run(
            ["gh", "auth", "status"],
            capture_output=True,
            check=False,
            timeout=10,
        )
        if result.returncode != 0:
            console.print("[red]❌ GitHub CLI is not authenticated[/red]")
            console.print("   Run: gh auth login")
            raise typer.Exit(code=1)
    except subprocess.TimeoutExpired:
        console.print("[red]❌ GitHub CLI authentication check timed out[/red]")
        raise typer.Exit(code=1)

    # Find most recent submission file
    console.print("[blue]📊 Finding submission file...[/blue]")

    submission_files = sorted(
        submission_dir.glob("ai_usage_*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )

    if not submission_files:
        console.print("[red]❌ No submission file found[/red]")
        console.print(f"   Expected files matching: {submission_dir}/ai_usage_*.json")
        console.print("   Run 'hermod collect' first to generate submission data")
        raise typer.Exit(code=1)

    submission_file = submission_files[0]
    console.print(f"[green]✓[/green] Found: {submission_file}")

    # Load and extract developer name
    try:
        with open(submission_file, "r") as f:
            data = json.load(f)
        developer = data["metadata"]["developer"]
    except (json.JSONDecodeError, KeyError) as e:
        console.print(f"[red]❌ Invalid submission file format: {e}[/red]")
        raise typer.Exit(code=1)

    # Base64 encode the data
    console.print("[blue]🔐 Encoding submission data...[/blue]")
    with open(submission_file, "rb") as f:
        data_b64 = base64.b64encode(f.read()).decode("utf-8")

    # Trigger GitHub Actions workflow
    console.print("[blue]🚀 Submitting to GitHub Actions...[/blue]")

    try:
        result = subprocess.run(
            [
                "gh",
                "workflow",
                "run",
                "ai-usage-ingestion.yml",
                "-f",
                f"developer={developer}",
                "-f",
                f"data_base64={data_b64}",
            ],
            capture_output=True,
            check=False,
            timeout=30,
        )

        if result.returncode != 0:
            console.print(f"[red]❌ Failed to submit to GitHub Actions[/red]")
            error_msg = result.stderr.decode() if isinstance(result.stderr, bytes) else result.stderr
            console.print(f"   Error: {error_msg}")
            raise typer.Exit(code=1)

    except subprocess.TimeoutExpired:
        console.print("[red]❌ GitHub Actions workflow trigger timed out[/red]")
        raise typer.Exit(code=1)

    # Get repository info for the success message
    try:
        result = subprocess.run(
            ["gh", "repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"],
            capture_output=True,
            check=True,
            timeout=10,
        )
        repo_name_bytes = result.stdout.decode() if isinstance(result.stdout, bytes) else result.stdout
        repo_name = repo_name_bytes.strip()
        actions_url = f"https://github.com/{repo_name}/actions"
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        actions_url = "GitHub Actions"

    console.print(f"[green]✅ Submitted![/green] Check {actions_url}")

    # Clean up submission file
    console.print("[blue]📝 Cleaning up local submission file...[/blue]")
    submission_file.unlink()
    console.print("[green]✓[/green] Done")


if __name__ == "__main__":
    app()

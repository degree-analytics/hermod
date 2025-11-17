"""AI usage data collection from ccusage and ccusage-codex."""

import json
import logging
import os
import subprocess  # nosec B404 - Legitimate CLI integration with validation
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Allowed commands for security
ALLOWED_COMMANDS = {"ccusage", "ccusage-codex"}

# Command execution timeout configuration (seconds)
DEFAULT_COMMAND_TIMEOUT_SECONDS = 60
MIN_COMMAND_TIMEOUT_SECONDS = 5
MAX_COMMAND_TIMEOUT_SECONDS = 900

# Default output directory (configurable via environment variable)
DEFAULT_OUTPUT_DIR = Path(os.getenv("HERMOD_OUTPUT_DIR", "data/ai_usage/submissions"))


def _validate_timeout(value: int) -> int:
    """Validate timeout bounds."""
    if value < MIN_COMMAND_TIMEOUT_SECONDS or value > MAX_COMMAND_TIMEOUT_SECONDS:
        raise ValueError(
            f"Timeout must be between {MIN_COMMAND_TIMEOUT_SECONDS} and "
            f"{MAX_COMMAND_TIMEOUT_SECONDS} seconds"
        )
    return value


def resolve_command_timeout_seconds(explicit_timeout: Optional[int] = None) -> int:
    """Resolve command timeout from explicit flag, env var, or defaults."""
    if explicit_timeout is not None:
        return _validate_timeout(explicit_timeout)

    env_value = os.getenv("HERMOD_COMMAND_TIMEOUT_SECONDS")
    if env_value:
        try:
            return _validate_timeout(int(env_value))
        except ValueError as err:
            logger.warning(
                "Invalid HERMOD_COMMAND_TIMEOUT_SECONDS=%s: %s. Falling back to default (%ss).",
                env_value,
                err,
                DEFAULT_COMMAND_TIMEOUT_SECONDS,
            )

    return DEFAULT_COMMAND_TIMEOUT_SECONDS


def run_command(cmd: list[str], timeout_seconds: Optional[int] = None) -> Dict[str, Any]:
    """Run command and return parsed JSON output with security validation.

    Args:
        cmd: Command and arguments to run
        timeout_seconds: Optional timeout override in seconds

    Returns:
        Parsed JSON output, or empty dict on error

    Raises:
        ValueError: If command or arguments are invalid
    """
    # Validate command is in allowlist
    if not cmd or cmd[0] not in ALLOWED_COMMANDS:
        raise ValueError(f"Command not allowed: {cmd[0] if cmd else 'empty'}")

    # Validate arguments don't contain shell injection characters
    dangerous_chars = {";", "|", "&", "$", "`", "(", ")", "<", ">", "\n", "\r"}
    for arg in cmd[1:]:
        if any(char in arg for char in dangerous_chars):
            raise ValueError(f"Invalid argument contains dangerous characters: {arg}")

    timeout = resolve_command_timeout_seconds(timeout_seconds)

    try:
        result = subprocess.run(  # nosec B603 - Command validated against allowlist
            cmd, capture_output=True, text=True, check=True, timeout=timeout
        )
        data = json.loads(result.stdout)

        # Validate output structure is a dictionary
        if not isinstance(data, dict):
            raise ValueError(f"Expected dict response, got {type(data).__name__}")

        return data

    except subprocess.TimeoutExpired:
        logger.error(f"Command timeout after {timeout}s: {cmd[0]}")
        return {}
    except subprocess.CalledProcessError as e:
        logger.warning(f"Command failed: {cmd[0]}: {e}")
        return {}
    except json.JSONDecodeError as e:
        logger.warning(f"Invalid JSON from {cmd[0]}: {e}")
        return {}
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise


def collect_usage(
    developer: str,
    days: int = 7,
    command_timeout_seconds: Optional[int] = None,
) -> Dict[str, Any]:
    """Collect usage data from both ccusage and ccusage-codex.

    Args:
        developer: Developer canonical name
        days: Number of days to collect (default: 7)
        command_timeout_seconds: Optional timeout override for each command

    Returns:
        Combined usage data with metadata

    Example:
        >>> data = collect_usage("Chad", days=7)
        >>> print(data["metadata"]["developer"])
        Chad
        >>> print(data["claude_code"]["totals"]["totalCost"])
        1.50
    """
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    since_str = start_date.strftime("%Y%m%d")

    # Collect Claude Code usage
    claude_data = run_command(
        ["ccusage", "daily", "--json", "--since", since_str],
        timeout_seconds=command_timeout_seconds,
    )

    # Collect Codex usage
    codex_data = run_command(
        ["ccusage-codex", "daily", "--json", "--since", since_str],
        timeout_seconds=command_timeout_seconds,
    )

    # Combine with metadata
    return {
        "metadata": {
            "developer": developer,
            "collected_at": datetime.now().isoformat(),
            "date_range": {
                "start": start_date.date().isoformat(),
                "end": end_date.date().isoformat(),
                "days": days,
            },
            "version": "1.0",
        },
        "claude_code": claude_data,
        "codex": codex_data,
    }


def save_submission(data: Dict[str, Any], developer: str, output_dir: Path = None) -> Path:
    """Save submission data to JSON file.

    Args:
        data: Usage data to save
        developer: Developer name for filename
        output_dir: Output directory (default: from HERMOD_OUTPUT_DIR env var
                    or data/ai_usage/submissions)

    Returns:
        Path to saved file

    Example:
        >>> from pathlib import Path
        >>> data = {"metadata": {"developer": "Chad"}, "claude_code": {}, "codex": {}}
        >>> output_path = save_submission(data, "Chad", output_dir=Path("/tmp"))
        >>> print(output_path.name)
        ai_usage_Chad_20251022_143000.json
    """
    if output_dir is None:
        output_dir = DEFAULT_OUTPUT_DIR

    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    date_str = datetime.now().strftime("%Y%m%d")
    output_file = output_dir / f"ai_usage_{developer}_{date_str}_{timestamp}.json"

    with open(output_file, "w") as f:
        json.dump(data, f, indent=2)

    return output_file

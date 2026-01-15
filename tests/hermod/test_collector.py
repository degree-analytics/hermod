"""Tests for AI usage data collection."""

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from hermod.collector import (
    DEFAULT_COMMAND_TIMEOUT_SECONDS,
    MAX_COMMAND_TIMEOUT_SECONDS,
    MIN_COMMAND_TIMEOUT_SECONDS,
    collect_usage,
    resolve_command_timeout_seconds,
    run_command,
    save_submission,
)


def test_collect_usage_success() -> None:
    """Test successful data collection."""
    with patch("hermod.collector.run_command") as mock_run:
        # Mock ccusage response
        mock_run.side_effect = [
            {"daily": [{"date": "2025-01-22", "cost": 1.50}], "totals": {"totalCost": 1.50}},
            {"daily": [{"date": "2025-01-22", "cost": 2.00}], "totals": {"totalCost": 2.00}},
        ]

        data = collect_usage("Chad", days=7)

        assert data["metadata"]["developer"] == "Chad"
        assert data["metadata"]["date_range"]["days"] == 7
        assert "claude_code" in data
        assert "codex" in data
        assert data["claude_code"]["totals"]["totalCost"] == 1.50
        assert data["codex"]["totals"]["totalCost"] == 2.00


def test_collect_usage_handles_errors() -> None:
    """Test collection continues when one tool fails."""
    with patch("hermod.collector.run_command") as mock_run:
        # First call succeeds, second fails
        mock_run.side_effect = [
            {"daily": [], "totals": {}},
            {},  # Empty dict indicates error
        ]

        data = collect_usage("Chad", days=7)

        assert data["claude_code"] == {"daily": [], "totals": {}}
        assert data["codex"] == {}


def test_save_submission() -> None:
    """Test saving submission to file."""
    import tempfile
    from pathlib import Path

    test_data = {
        "metadata": {"developer": "Chad", "collected_at": "2025-01-22T10:00:00"},
        "claude_code": {},
        "codex": {},
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = save_submission(test_data, "Chad", output_dir=Path(tmpdir))

        assert output_path.exists()
        assert "ai_usage_Chad_" in output_path.name
        assert output_path.suffix == ".json"

        # Verify content
        import json

        with open(output_path) as f:
            loaded = json.load(f)
        assert loaded["metadata"]["developer"] == "Chad"


def test_run_command_validates_allowed_commands() -> None:
    """Test that only allowed commands can be run."""
    with pytest.raises(ValueError, match="Command not allowed"):
        run_command(["malicious-command", "--arg"])


def test_run_command_validates_empty_command() -> None:
    """Test that empty command list is rejected."""
    with pytest.raises(ValueError, match="Command not allowed"):
        run_command([])


def test_run_command_validates_dangerous_arguments() -> None:
    """Test that dangerous shell characters are rejected."""
    dangerous_commands = [
        ["ccusage", "daily", "; rm -rf /"],
        ["ccusage", "daily", "| cat /etc/passwd"],
        ["ccusage", "daily", "& background-task"],
        ["ccusage", "daily", "$(malicious)"],
        ["ccusage", "daily", "`whoami`"],
    ]

    for cmd in dangerous_commands:
        with pytest.raises(ValueError, match="Invalid argument contains dangerous characters"):
            run_command(cmd)


def test_run_command_success() -> None:
    """Test successful command execution."""
    with patch("subprocess.run") as mock_run:
        mock_result = MagicMock()
        mock_result.stdout = '{"daily": [], "totals": {}}'
        mock_run.return_value = mock_result

        result = run_command(["ccusage", "daily", "--json"])

        assert result == {"daily": [], "totals": {}}
        mock_run.assert_called_once()
        # Verify timeout is set
        assert mock_run.call_args[1]["timeout"] == DEFAULT_COMMAND_TIMEOUT_SECONDS


def test_run_command_respects_explicit_timeout() -> None:
    """Test explicit timeout override is applied."""
    with patch("subprocess.run") as mock_run:
        mock_result = MagicMock()
        mock_result.stdout = '{"daily": [], "totals": {}}'
        mock_run.return_value = mock_result

        result = run_command(["ccusage", "daily"], timeout_seconds=300)

        assert result == {"daily": [], "totals": {}}
        assert mock_run.call_args[1]["timeout"] == 300


def test_resolve_command_timeout_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test timeout can be configured via environment variable."""
    monkeypatch.setenv("HERMOD_COMMAND_TIMEOUT_SECONDS", "120")
    try:
        resolved = resolve_command_timeout_seconds()
        assert resolved == 120
    finally:
        monkeypatch.delenv("HERMOD_COMMAND_TIMEOUT_SECONDS", raising=False)


def test_resolve_command_timeout_invalid_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test invalid env values fall back to default."""
    monkeypatch.setenv("HERMOD_COMMAND_TIMEOUT_SECONDS", "9999")
    try:
        resolved = resolve_command_timeout_seconds()
        assert resolved == DEFAULT_COMMAND_TIMEOUT_SECONDS
    finally:
        monkeypatch.delenv("HERMOD_COMMAND_TIMEOUT_SECONDS", raising=False)


def test_resolve_command_timeout_explicit_bounds() -> None:
    """Explicit timeout values must respect configured bounds."""
    with pytest.raises(ValueError):
        resolve_command_timeout_seconds(MIN_COMMAND_TIMEOUT_SECONDS - 1)

    with pytest.raises(ValueError):
        resolve_command_timeout_seconds(MAX_COMMAND_TIMEOUT_SECONDS + 1)

    assert (
        resolve_command_timeout_seconds(MIN_COMMAND_TIMEOUT_SECONDS + 1)
        == MIN_COMMAND_TIMEOUT_SECONDS + 1
    )


def test_run_command_timeout() -> None:
    """Test command timeout handling."""
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.TimeoutExpired("ccusage", DEFAULT_COMMAND_TIMEOUT_SECONDS)

        result = run_command(["ccusage", "daily"])

        assert result == {}


def test_run_command_invalid_json() -> None:
    """Test handling of invalid JSON response."""
    with patch("subprocess.run") as mock_run:
        mock_result = MagicMock()
        mock_result.stdout = "not valid json"
        mock_run.return_value = mock_result

        result = run_command(["ccusage", "daily"])

        assert result == {}


def test_run_command_non_dict_response() -> None:
    """Test validation rejects non-dict JSON responses."""
    with patch("subprocess.run") as mock_run:
        mock_result = MagicMock()
        mock_result.stdout = '["list", "not", "dict"]'
        mock_run.return_value = mock_result

        with pytest.raises(ValueError, match="Expected dict response"):
            run_command(["ccusage", "daily"])


def test_run_command_called_process_error() -> None:
    """Test handling of CalledProcessError (command failure)."""
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.CalledProcessError(
            returncode=1, cmd=["ccusage", "daily"], stderr="Command failed"
        )

        result = run_command(["ccusage", "daily"])

        assert result == {}

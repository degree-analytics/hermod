"""Tests for Hermod CLI."""

from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from hermod.cli import app


@pytest.fixture
def runner() -> CliRunner:
    """CLI test runner."""
    return CliRunner()


def test_collect_command_with_defaults(runner: CliRunner) -> None:
    """Test collect command with default values."""
    with patch("hermod.cli.detect_developer", return_value="Chad"):
        with patch(
            "hermod.cli.check_all_dependencies",
            return_value={"ccusage": True, "ccusage-codex": True},
        ):
            with patch("hermod.cli.collect_usage") as mock_collect:
                with patch("hermod.cli.save_submission") as mock_save:
                    from pathlib import Path

                    mock_save.return_value = Path("test.json")
                    mock_collect.return_value = {
                        "metadata": {
                            "developer": "Chad",
                            "date_range": {"start": "2025-01-15", "end": "2025-01-22"},
                        },
                        "claude_code": {"totals": {"totalCost": 1.5}},
                        "codex": {"totals": {"totalCost": 2.0}},
                    }

                    result = runner.invoke(app, ["collect"])

                    assert result.exit_code == 0
                    assert "Chad" in result.stdout
                    mock_collect.assert_called_once_with("Chad", 7, command_timeout_seconds=None)


def test_collect_command_with_custom_developer(runner: CliRunner) -> None:
    """Test collect command with explicit developer."""
    with patch(
        "hermod.cli.check_all_dependencies", return_value={"ccusage": True, "ccusage-codex": True}
    ):
        with patch("hermod.cli.collect_usage") as mock_collect:
            with patch("hermod.cli.save_submission") as mock_save:
                from pathlib import Path

                mock_save.return_value = Path("test.json")
                mock_collect.return_value = {
                    "metadata": {
                        "developer": "Eugene",
                        "date_range": {"start": "2025-01-15", "end": "2025-01-22"},
                    },
                    "claude_code": {"totals": {"totalCost": 1.5}},
                    "codex": {"totals": {"totalCost": 2.0}},
                }

                result = runner.invoke(app, ["collect", "--developer", "Eugene"])

                assert result.exit_code == 0
                mock_collect.assert_called_once_with("Eugene", 7, command_timeout_seconds=None)


def test_collect_command_missing_dependencies(runner: CliRunner) -> None:
    """Test collect command when dependencies are missing."""
    with patch("hermod.cli.detect_developer", return_value="Chad"):
        with patch(
            "hermod.cli.check_all_dependencies",
            return_value={"ccusage": False, "ccusage-codex": True},
        ):
            result = runner.invoke(app, ["collect"])

            assert result.exit_code == 1
            assert "not installed" in result.stdout.lower()


def test_collect_command_json_output(runner: CliRunner) -> None:
    """Test JSON output mode."""
    with patch("hermod.cli.detect_developer", return_value="Chad"):
        with patch(
            "hermod.cli.check_all_dependencies",
            return_value={"ccusage": True, "ccusage-codex": True},
        ):
            with patch("hermod.cli.collect_usage") as mock_collect:
                with patch("hermod.cli.save_submission") as mock_save:
                    from pathlib import Path

                    mock_save.return_value = Path("test.json")
                    test_data = {
                        "metadata": {"developer": "Chad"},
                        "claude_code": {"totals": {"totalCost": 1.5}},
                        "codex": {"totals": {"totalCost": 2.0}},
                    }
                    mock_collect.return_value = test_data

                    result = runner.invoke(app, ["collect", "--json"])

                    assert result.exit_code == 0
                    import json

                    output = json.loads(result.stdout)
                    assert output["developer"] == "Chad"
                    assert output["timeout_seconds"] is None


def test_collect_command_invalid_developer_name(runner: CliRunner) -> None:
    """Test validation rejects invalid developer names."""
    with patch(
        "hermod.cli.check_all_dependencies", return_value={"ccusage": True, "ccusage-codex": True}
    ):
        # Test with special characters
        result = runner.invoke(app, ["collect", "--developer", "user@domain.com"])
        assert result.exit_code == 1
        assert "Invalid developer name" in result.stdout

        # Test with too long name
        result = runner.invoke(app, ["collect", "--developer", "a" * 101])
        assert result.exit_code == 1
        assert "Invalid developer name" in result.stdout

        # Test with empty string
        result = runner.invoke(app, ["collect", "--developer", ""])
        assert result.exit_code == 1
        assert "Invalid developer name" in result.stdout


def test_collect_command_invalid_days_parameter(runner: CliRunner) -> None:
    """Test validation rejects invalid days values."""
    with patch("hermod.cli.detect_developer", return_value="Chad"):
        with patch(
            "hermod.cli.check_all_dependencies",
            return_value={"ccusage": True, "ccusage-codex": True},
        ):
            # Test with days < 1
            result = runner.invoke(app, ["collect", "--days", "0"])
            assert result.exit_code == 2  # Typer validation error
            # Typer outputs validation errors to stderr or stdout depending on version
            output = result.stdout + result.stderr if hasattr(result, "stderr") else result.stdout
            assert (
                "Invalid value" in output
                or "out of range" in output.lower()
                or result.exit_code == 2
            )

            # Test with days > 365
            result = runner.invoke(app, ["collect", "--days", "366"])
            assert result.exit_code == 2  # Typer validation error
            output = result.stdout + result.stderr if hasattr(result, "stderr") else result.stdout
            assert (
                "Invalid value" in output
                or "out of range" in output.lower()
                or result.exit_code == 2
            )


def test_collect_command_valid_developer_names(runner: CliRunner) -> None:
    """Test validation accepts valid developer names."""
    with patch(
        "hermod.cli.check_all_dependencies", return_value={"ccusage": True, "ccusage-codex": True}
    ):
        with patch("hermod.cli.collect_usage") as mock_collect:
            with patch("hermod.cli.save_submission") as mock_save:
                from pathlib import Path

                mock_save.return_value = Path("test.json")
                mock_collect.return_value = {
                    "metadata": {
                        "developer": "Chad",
                        "date_range": {"start": "2025-01-15", "end": "2025-01-22"},
                    },
                    "claude_code": {"totals": {"totalCost": 1.5}},
                    "codex": {"totals": {"totalCost": 2.0}},
                }

                # Test valid names
                valid_names = ["Chad", "Chad Walters", "Chad_W", "Chad-W", "ChadW123"]
                for name in valid_names:
                    result = runner.invoke(app, ["collect", "--developer", name])
                    assert result.exit_code == 0, f"Failed for name: {name}"


def test_collect_command_auto_detect_invalid_name(runner: CliRunner) -> None:
    """Test validation rejects auto-detected invalid names."""
    with patch("hermod.cli.detect_developer", return_value="invalid@email.com"):
        with patch(
            "hermod.cli.check_all_dependencies",
            return_value={"ccusage": True, "ccusage-codex": True},
        ):
            result = runner.invoke(app, ["collect"])
            assert result.exit_code == 1
            assert "Auto-detected developer name" in result.stdout
            assert "invalid" in result.stdout


def test_collect_command_with_timeout_override(runner: CliRunner) -> None:
    """Test the timeout override flag is passed through."""
    with patch("hermod.cli.detect_developer", return_value="Chad"):
        with patch(
            "hermod.cli.check_all_dependencies",
            return_value={"ccusage": True, "ccusage-codex": True},
        ):
            with patch("hermod.cli.collect_usage") as mock_collect:
                with patch("hermod.cli.save_submission") as mock_save:
                    from pathlib import Path

                    mock_save.return_value = Path("test.json")
                    mock_collect.return_value = {
                        "metadata": {
                            "developer": "Chad",
                            "date_range": {"start": "2025-01-15", "end": "2025-01-22"},
                        },
                        "claude_code": {"totals": {"totalCost": 1.5}},
                        "codex": {"totals": {"totalCost": 2.0}},
                    }

                result = runner.invoke(app, ["collect", "--timeout", "300"])

                assert result.exit_code == 0
                mock_collect.assert_called_once_with("Chad", 7, command_timeout_seconds=300)
                assert "Command timeout override" in result.stdout


def test_submit_command_success(tmp_path):
    """Test submit command successfully submits data to GitHub Actions."""
    # Create a fake submission file
    submission_data = {
        "metadata": {
            "developer": "test-developer",
            "date_range": {"start": "2025-11-10", "end": "2025-11-17"},
        },
        "claude_code": {"totals": {"totalCost": 5.0}},
        "codex": {"totals": {"totalCost": 3.0}},
    }
    submission_file = tmp_path / "ai_usage_test.json"
    import json
    submission_file.write_text(json.dumps(submission_data))

    with patch("hermod.cli.subprocess.run") as mock_run:
        # Mock gh auth status (success)
        # Mock gh workflow run (success)
        from unittest.mock import MagicMock
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        with patch("hermod.cli.Path.glob") as mock_glob:
            mock_glob.return_value = [submission_file]

            from typer.testing import CliRunner
            from hermod.cli import app

            runner = CliRunner()
            result = runner.invoke(app, ["submit"])

            assert result.exit_code == 0
            assert "Submitted!" in result.stdout
            assert not submission_file.exists()  # File should be deleted after submission


def test_submit_command_no_gh_cli():
    """Test submit command fails gracefully when gh CLI not installed."""
    import shutil
    with patch("shutil.which", return_value=None):
        from typer.testing import CliRunner
        from hermod.cli import app

        runner = CliRunner()
        result = runner.invoke(app, ["submit"])

        assert result.exit_code == 1
        assert "GitHub CLI (gh) is not installed" in result.stdout


def test_submit_command_gh_not_authenticated():
    """Test submit command fails when gh CLI not authenticated."""
    import shutil
    with patch("shutil.which", return_value="/usr/local/bin/gh"):
        with patch("hermod.cli.subprocess.run") as mock_run:
            # gh auth status returns non-zero when not authenticated
            from unittest.mock import MagicMock
            mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="not logged in")

            from typer.testing import CliRunner
            from hermod.cli import app

            runner = CliRunner()
            result = runner.invoke(app, ["submit"])

            assert result.exit_code == 1
            assert "GitHub CLI is not authenticated" in result.stdout


def test_submit_command_no_submission_file():
    """Test submit command fails when no submission file found."""
    import shutil
    with patch("shutil.which", return_value="/usr/local/bin/gh"):
        with patch("hermod.cli.subprocess.run") as mock_run:
            from unittest.mock import MagicMock
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

            with patch("hermod.cli.Path.glob", return_value=[]):
                from typer.testing import CliRunner
                from hermod.cli import app

                runner = CliRunner()
                result = runner.invoke(app, ["submit"])

                assert result.exit_code == 1
                assert "No submission file found" in result.stdout

"""Tests for Hermod CLI."""

import json
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from hermod.cli import app


@pytest.fixture
def runner() -> CliRunner:
    """CLI test runner."""
    return CliRunner()


def test_version_flag_shows_version() -> None:
    """Test --version flag displays the current package version."""
    from hermod.__version__ import __version__

    runner = CliRunner()
    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert __version__ in result.stdout


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
    with patch("shutil.which", return_value=None):
        from typer.testing import CliRunner

        from hermod.cli import app

        runner = CliRunner()
        result = runner.invoke(app, ["submit"])

        assert result.exit_code == 1
        assert "GitHub CLI (gh) is not installed" in result.stdout


def test_submit_command_gh_not_authenticated():
    """Test submit command fails when gh CLI not authenticated."""
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


# === Additional coverage tests ===


def test_collect_command_invalid_developer_json_output():
    """Test invalid developer name error in JSON output mode."""
    runner = CliRunner()
    result = runner.invoke(app, ["collect", "--developer", "user@invalid.com", "--json"])

    assert result.exit_code == 1
    # JSON output contains error key with the message
    assert '"error"' in result.stdout
    assert "Invalid developer name" in result.stdout


def test_collect_command_missing_deps_json_output():
    """Test missing dependencies error in JSON output mode."""
    with patch(
        "hermod.cli.check_all_dependencies",
        return_value={"ccusage": False, "ccusage-codex": False},
    ):
        runner = CliRunner()
        result = runner.invoke(app, ["collect", "--developer", "Test", "--json"])

        assert result.exit_code == 1
        output = json.loads(result.stdout)
        assert "error" in output
        assert "Dependencies not installed" in output["error"]


def test_collect_command_developer_detection_failure_json():
    """Test developer auto-detection failure in JSON output mode."""
    with patch(
        "hermod.cli.check_all_dependencies",
        return_value={"ccusage": True, "ccusage-codex": True},
    ):
        with patch("hermod.cli.detect_developer", side_effect=RuntimeError("Git not configured")):
            runner = CliRunner()
            result = runner.invoke(app, ["collect", "--json"])

            assert result.exit_code == 1
            output = json.loads(result.stdout)
            assert "error" in output
            assert "Failed to detect developer" in output["error"]


def test_collect_command_auto_detect_invalid_name_json():
    """Test auto-detected invalid developer name in JSON output mode."""
    with patch(
        "hermod.cli.check_all_dependencies",
        return_value={"ccusage": True, "ccusage-codex": True},
    ):
        with patch("hermod.cli.detect_developer", return_value="!!!invalid!!!"):
            runner = CliRunner()
            result = runner.invoke(app, ["collect", "--json"])

            assert result.exit_code == 1
            # JSON output contains error key with the message
            assert '"error"' in result.stdout
            assert "invalid" in result.stdout.lower()


def test_collect_command_usage_collection_failure_json():
    """Test usage collection failure in JSON output mode."""
    with patch(
        "hermod.cli.check_all_dependencies",
        return_value={"ccusage": True, "ccusage-codex": True},
    ):
        with patch("hermod.cli.detect_developer", return_value="TestDev"):
            with patch("hermod.cli.collect_usage", side_effect=Exception("ccusage failed")):
                runner = CliRunner()
                result = runner.invoke(app, ["collect", "--json"])

                assert result.exit_code == 1
                output = json.loads(result.stdout)
                assert "error" in output
                assert "Failed to collect usage data" in output["error"]


def test_collect_command_save_failure_json():
    """Test save submission failure in JSON output mode."""

    mock_data = {
        "metadata": {"date_range": {"start": "2026-01-01", "end": "2026-01-07"}},
        "claude_code": {},
        "codex": {},
    }

    with patch(
        "hermod.cli.check_all_dependencies",
        return_value={"ccusage": True, "ccusage-codex": True},
    ):
        with patch("hermod.cli.detect_developer", return_value="TestDev"):
            with patch("hermod.cli.collect_usage", return_value=mock_data):
                with patch("hermod.cli.save_submission", side_effect=Exception("Disk full")):
                    runner = CliRunner()
                    result = runner.invoke(app, ["collect", "--json"])

                    assert result.exit_code == 1
                    output = json.loads(result.stdout)
                    assert "error" in output
                    assert "Failed to save submission" in output["error"]


def test_collect_command_shows_env_timeout(monkeypatch):
    """Test that env var timeout is displayed in output."""
    from pathlib import Path

    monkeypatch.setenv("HERMOD_COMMAND_TIMEOUT_SECONDS", "120")

    mock_data = {
        "metadata": {"date_range": {"start": "2026-01-01", "end": "2026-01-07"}},
        "claude_code": {"totals": {"totalCost": 1.50}},
        "codex": {"totals": {"totalCost": 0.50}},
    }

    with patch(
        "hermod.cli.check_all_dependencies",
        return_value={"ccusage": True, "ccusage-codex": True},
    ):
        with patch("hermod.cli.detect_developer", return_value="TestDev"):
            with patch("hermod.cli.collect_usage", return_value=mock_data):
                with patch(
                    "hermod.cli.save_submission",
                    return_value=Path("data/submissions/test.json"),
                ):
                    runner = CliRunner()
                    result = runner.invoke(app, ["collect"])

                    assert result.exit_code == 0
                    assert "HERMOD_COMMAND_TIMEOUT_SECONDS" in result.stdout


def test_collect_command_codex_cost_usd_fallback():
    """Test codex costUSD fallback when totalCost is missing."""
    from pathlib import Path

    mock_data = {
        "metadata": {"date_range": {"start": "2026-01-01", "end": "2026-01-07"}},
        "claude_code": {"totals": {"totalCost": 1.50}},
        "codex": {"totals": {"costUSD": 0.75}},  # Note: costUSD not totalCost
    }

    with patch(
        "hermod.cli.check_all_dependencies",
        return_value={"ccusage": True, "ccusage-codex": True},
    ):
        with patch("hermod.cli.detect_developer", return_value="TestDev"):
            with patch("hermod.cli.collect_usage", return_value=mock_data):
                with patch(
                    "hermod.cli.save_submission",
                    return_value=Path("data/submissions/test.json"),
                ):
                    runner = CliRunner()
                    result = runner.invoke(app, ["collect"])

                    assert result.exit_code == 0
                    assert "$0.75" in result.stdout or "0.75" in result.stdout


def test_submit_command_gh_auth_timeout():
    """Test submit command handles gh auth timeout."""
    import subprocess

    with patch("shutil.which", return_value="/usr/bin/gh"):
        with patch("hermod.cli.subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(cmd="gh auth status", timeout=10)

            runner = CliRunner()
            result = runner.invoke(app, ["submit"])

            assert result.exit_code == 1
            assert "timed out" in result.stdout.lower()


def test_submit_command_invalid_json_file(tmp_path):
    """Test submit command handles invalid JSON in submission file."""
    from unittest.mock import MagicMock

    # Create invalid JSON file
    submission_dir = tmp_path / "submissions"
    submission_dir.mkdir()
    invalid_file = submission_dir / "ai_usage_test_20260115_120000.json"
    invalid_file.write_text("not valid json {{{")

    with patch("shutil.which", return_value="/usr/bin/gh"):
        with patch("hermod.cli.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            runner = CliRunner()
            result = runner.invoke(app, ["submit", "--submission-dir", str(submission_dir)])

            assert result.exit_code == 1
            assert "Invalid submission file format" in result.stdout


def test_submit_command_workflow_trigger_failure(tmp_path):
    """Test submit command handles workflow trigger failure."""
    from unittest.mock import MagicMock

    # Create valid submission file
    submission_dir = tmp_path / "submissions"
    submission_dir.mkdir()
    valid_file = submission_dir / "ai_usage_test_20260115_120000.json"
    valid_file.write_text('{"metadata": {"developer": "TestDev"}}')

    with patch("shutil.which", return_value="/usr/bin/gh"):
        with patch("hermod.cli.subprocess.run") as mock_run:
            # First call: gh auth status succeeds
            # Second call: gh workflow run fails
            mock_run.side_effect = [
                MagicMock(returncode=0),  # auth status
                MagicMock(returncode=1, stderr=b"workflow not found"),  # workflow run
            ]

            runner = CliRunner()
            result = runner.invoke(app, ["submit", "--submission-dir", str(submission_dir)])

            assert result.exit_code == 1
            assert "Failed to submit" in result.stdout


def test_submit_command_workflow_timeout(tmp_path):
    """Test submit command handles workflow trigger timeout."""
    import subprocess
    from unittest.mock import MagicMock

    # Create valid submission file
    submission_dir = tmp_path / "submissions"
    submission_dir.mkdir()
    valid_file = submission_dir / "ai_usage_test_20260115_120000.json"
    valid_file.write_text('{"metadata": {"developer": "TestDev"}}')

    with patch("shutil.which", return_value="/usr/bin/gh"):
        with patch("hermod.cli.subprocess.run") as mock_run:
            # First call: gh auth status succeeds
            # Second call: gh workflow run times out
            mock_run.side_effect = [
                MagicMock(returncode=0),  # auth status
                subprocess.TimeoutExpired(cmd="gh workflow run", timeout=30),  # workflow run
            ]

            runner = CliRunner()
            result = runner.invoke(app, ["submit", "--submission-dir", str(submission_dir)])

            assert result.exit_code == 1
            assert "timed out" in result.stdout.lower()


def test_submit_command_repo_view_failure_fallback(tmp_path):
    """Test submit command handles repo view failure gracefully."""
    import subprocess
    from unittest.mock import MagicMock

    # Create valid submission file
    submission_dir = tmp_path / "submissions"
    submission_dir.mkdir()
    valid_file = submission_dir / "ai_usage_test_20260115_120000.json"
    valid_file.write_text('{"metadata": {"developer": "TestDev"}}')

    with patch("shutil.which", return_value="/usr/bin/gh"):
        with patch("hermod.cli.subprocess.run") as mock_run:
            mock_run.side_effect = [
                MagicMock(returncode=0),  # auth status
                MagicMock(returncode=0),  # workflow run
                subprocess.CalledProcessError(1, "gh repo view"),  # repo view fails
            ]

            runner = CliRunner()
            result = runner.invoke(app, ["submit", "--submission-dir", str(submission_dir)])

            assert result.exit_code == 0
            assert "Submitted" in result.stdout
            assert "GitHub Actions" in result.stdout  # Fallback text

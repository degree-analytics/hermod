"""Tests for git configuration detection."""

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from hermod.git_detector import detect_developer, get_git_user_email


def test_get_git_user_email_success() -> None:
    """Test extracting email from git config."""
    with patch("subprocess.run") as mock_run:
        mock_result = MagicMock()
        mock_result.stdout = "chad@degreeanalytics.com\n"
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        email = get_git_user_email()
        assert email == "chad@degreeanalytics.com"
        mock_run.assert_called_once_with(
            ["git", "config", "user.email"], capture_output=True, text=True, check=True
        )


def test_get_git_user_email_not_configured() -> None:
    """Test handling when git email is not configured."""
    import subprocess

    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.CalledProcessError(1, "git config")

        with pytest.raises(RuntimeError, match="Git user.email not configured"):
            get_git_user_email()


def test_detect_developer_from_git_name() -> None:
    """Test detecting canonical name from git name."""
    mock_mappings = {
        "email_to_canonical": {},
        "name_to_canonical": {"chad walters": "Chad"},
    }
    with patch("hermod.git_detector.load_developer_mappings", return_value=mock_mappings):
        with patch("hermod.git_detector.get_git_user_email", return_value="unknown@example.com"):
            with patch("subprocess.run") as mock_run:
                mock_result = MagicMock()
                mock_result.stdout = "Chad Walters\n"
                mock_result.returncode = 0
                mock_run.return_value = mock_result

                developer = detect_developer()
                assert developer == "Chad"


def test_detect_developer_from_email() -> None:
    """Test detecting canonical name from git email."""
    mock_mappings = {
        "email_to_canonical": {"chad.walters@campusiq.com": "Chad"},
        "name_to_canonical": {},
    }
    with patch("hermod.git_detector.load_developer_mappings", return_value=mock_mappings):
        with patch(
            "hermod.git_detector.get_git_user_email", return_value="chad.walters@campusiq.com"
        ):
            developer = detect_developer()
            assert developer == "Chad"


def test_detect_developer_email_fallback() -> None:
    """Test fallback when developer not found in mappings."""
    mock_mappings = {"email_to_canonical": {}, "name_to_canonical": {}}
    with patch("hermod.git_detector.load_developer_mappings", return_value=mock_mappings):
        with patch("hermod.git_detector.get_git_user_email", return_value="unknown@example.com"):
            with patch("subprocess.run") as mock_run:
                # Raise CalledProcessError (one of the specific exceptions handled)
                mock_run.side_effect = subprocess.CalledProcessError(
                    1, ["git", "config", "user.name"]
                )

                developer = detect_developer()
                assert developer == "unknown"  # Email username fallback


# === Additional coverage tests ===


def test_get_git_user_name_timeout() -> None:
    """Test handling when git user.name command times out."""
    from hermod.git_detector import get_git_user_name

    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="git config user.name", timeout=5)

        result = get_git_user_name()
        assert result is None


def test_get_git_user_name_git_not_found() -> None:
    """Test handling when git is not installed."""
    from hermod.git_detector import get_git_user_name

    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = FileNotFoundError("git not found")

        result = get_git_user_name()
        assert result is None


def test_load_developer_mappings_with_config_file(tmp_path, monkeypatch) -> None:
    """Test loading developer mappings from config file."""
    import json

    import hermod.git_detector as gd

    config_data = {
        "developers": [
            {
                "canonical_name": "Alice",
                "git_emails": ["alice@example.com"],
                "git_names": ["Alice Smith"],
                "linear_names": ["alice@linear.com"],
            },
        ]
    }

    # Create directory structure matching the code's expectation
    # Path(__file__).parent.parent.parent / "config" / "developer_names.json"
    src_dir = tmp_path / "src" / "hermod"
    src_dir.mkdir(parents=True)
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    config_file = config_dir / "developer_names.json"
    config_file.write_text(json.dumps(config_data))

    # Patch __file__ to our temp structure
    monkeypatch.setattr(gd, "__file__", str(src_dir / "git_detector.py"))

    mappings = gd.load_developer_mappings()

    assert mappings["email_to_canonical"]["alice@example.com"] == "Alice"
    assert mappings["name_to_canonical"]["alice smith"] == "Alice"
    assert mappings["email_to_canonical"]["alice@linear.com"] == "Alice"


def test_detect_developer_raises_when_no_valid_fallback() -> None:
    """Test detect_developer raises RuntimeError when email username is invalid."""
    mock_mappings = {"email_to_canonical": {}, "name_to_canonical": {}}

    with patch("hermod.git_detector.load_developer_mappings", return_value=mock_mappings):
        with patch("hermod.git_detector.get_git_user_email", return_value="123@example.com"):
            with patch("hermod.git_detector.get_git_user_name", return_value=None):
                with pytest.raises(RuntimeError, match="Could not auto-detect developer"):
                    detect_developer()

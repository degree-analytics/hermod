"""Tests for external dependency checking."""

from unittest.mock import patch

from hermod.dependencies import (
    check_all_dependencies,
    check_ccusage_codex_installed,
    check_ccusage_installed,
)


def test_check_ccusage_installed_success() -> None:
    """Test detecting installed ccusage."""
    with patch("shutil.which", return_value="/usr/local/bin/ccusage"):
        is_installed = check_ccusage_installed()
        assert is_installed is True


def test_check_ccusage_installed_missing() -> None:
    """Test detecting missing ccusage."""
    with patch("shutil.which", return_value=None):
        is_installed = check_ccusage_installed()
        assert is_installed is False


def test_check_all_dependencies_success() -> None:
    """Test when all dependencies are installed."""
    with patch("hermod.dependencies.check_ccusage_installed", return_value=True):
        with patch("hermod.dependencies.check_ccusage_codex_installed", return_value=True):
            result = check_all_dependencies()
            assert result == {"ccusage": True, "ccusage-codex": True}


def test_check_all_dependencies_missing() -> None:
    """Test when dependencies are missing."""
    with patch("hermod.dependencies.check_ccusage_installed", return_value=False):
        with patch("hermod.dependencies.check_ccusage_codex_installed", return_value=False):
            result = check_all_dependencies()
            assert result == {"ccusage": False, "ccusage-codex": False}


def test_check_ccusage_codex_installed_success() -> None:
    """Test detecting installed ccusage-codex."""
    with patch("shutil.which", return_value="/usr/local/bin/ccusage-codex"):
        is_installed = check_ccusage_codex_installed()
        assert is_installed is True


def test_check_ccusage_codex_installed_missing() -> None:
    """Test detecting missing ccusage-codex."""
    with patch("shutil.which", return_value=None):
        is_installed = check_ccusage_codex_installed()
        assert is_installed is False

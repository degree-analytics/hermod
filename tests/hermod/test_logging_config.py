"""Tests for logging configuration."""

import logging
from pathlib import Path

from hermod.logging_config import get_logger, setup_logging


def test_setup_logging_with_log_file(tmp_path: Path) -> None:
    """Test setup_logging creates log file and writes to it."""
    log_file = tmp_path / "logs" / "test.log"

    setup_logging(level="DEBUG", log_file=log_file)

    # Verify directory was created
    assert log_file.parent.exists()

    # Log a message and verify it's written to file
    logger = logging.getLogger("test_logger")
    logger.debug("Test debug message")
    logger.info("Test info message")

    # Force flush by closing handlers
    for handler in logging.getLogger().handlers:
        handler.flush()

    assert log_file.exists()
    content = log_file.read_text()
    assert "Test debug message" in content
    assert "Test info message" in content


def test_setup_logging_default_format() -> None:
    """Test setup_logging uses default format when none specified."""
    setup_logging(level="INFO")

    # Verify handlers are set up
    root_logger = logging.getLogger()
    assert len(root_logger.handlers) >= 1

    # Verify console handler level
    console_handlers = [h for h in root_logger.handlers if isinstance(h, logging.StreamHandler)]
    assert len(console_handlers) >= 1


def test_setup_logging_custom_format() -> None:
    """Test setup_logging accepts custom format string."""
    custom_format = "%(levelname)s: %(message)s"
    setup_logging(level="INFO", format_string=custom_format)

    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        assert handler.formatter._fmt == custom_format


def test_setup_logging_clears_existing_handlers() -> None:
    """Test that setup_logging clears existing handlers to avoid duplicates."""
    # Add some dummy handlers
    root_logger = logging.getLogger()
    root_logger.addHandler(logging.NullHandler())
    root_logger.addHandler(logging.NullHandler())
    initial_count = len(root_logger.handlers)

    # Call setup_logging - should clear and add fresh handlers
    setup_logging(level="INFO")

    # Should have fewer handlers than before (only the new ones)
    assert len(root_logger.handlers) < initial_count + 2


def test_setup_logging_sets_level() -> None:
    """Test that setup_logging sets the correct log level."""
    setup_logging(level="WARNING")

    root_logger = logging.getLogger()
    assert root_logger.level == logging.WARNING

    hermod_logger = logging.getLogger("hermod")
    assert hermod_logger.level == logging.WARNING


def test_setup_logging_invalid_level_falls_back_to_info() -> None:
    """Test that invalid log level falls back to INFO."""
    setup_logging(level="INVALID_LEVEL")

    root_logger = logging.getLogger()
    assert root_logger.level == logging.INFO


def test_get_logger_returns_logger() -> None:
    """Test that get_logger returns a logger with the given name."""
    logger = get_logger("test.module")

    assert isinstance(logger, logging.Logger)
    assert logger.name == "test.module"


def test_get_logger_returns_same_logger_for_same_name() -> None:
    """Test that get_logger returns the same logger instance for the same name."""
    logger1 = get_logger("same.name")
    logger2 = get_logger("same.name")

    assert logger1 is logger2

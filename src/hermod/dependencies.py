"""External dependency checking for ccusage tools."""

import logging
import shutil
from typing import Dict

logger = logging.getLogger(__name__)


def check_ccusage_installed() -> bool:
    """Check if ccusage is installed and available on PATH.

    Returns:
        True if ccusage is installed, False otherwise
    """
    installed = shutil.which("ccusage") is not None
    if not installed:
        logger.warning("ccusage not found in PATH")
    return installed


def check_ccusage_codex_installed() -> bool:
    """Check if ccusage-codex is installed and available on PATH.

    Returns:
        True if ccusage-codex is installed, False otherwise
    """
    installed = shutil.which("ccusage-codex") is not None
    if not installed:
        logger.warning("ccusage-codex not found in PATH")
    return installed


def check_all_dependencies() -> Dict[str, bool]:
    """Check all required external dependencies.

    Returns:
        Dictionary mapping tool name to installed status

    Example:
        >>> deps = check_all_dependencies()
        >>> print(deps)
        {'ccusage': True, 'ccusage-codex': True}
        >>> all(deps.values())
        True
    """
    deps = {"ccusage": check_ccusage_installed(), "ccusage-codex": check_ccusage_codex_installed()}

    missing = [tool for tool, installed in deps.items() if not installed]
    if missing:
        logger.error(f"Missing dependencies: {', '.join(missing)}")
    else:
        logger.debug("All dependencies installed")

    return deps

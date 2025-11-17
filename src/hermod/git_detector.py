"""Git configuration detection for developer identification."""

import json
import logging
import subprocess  # nosec B404 - Legitimate git CLI integration
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Git command timeout in seconds
GIT_COMMAND_TIMEOUT_SECONDS = 5


def get_git_user_email() -> str:
    """Get user email from git config.

    Returns:
        Email address from git config

    Raises:
        RuntimeError: If git email is not configured
    """
    try:
        result = subprocess.run(  # nosec B603, B607 - Controlled git CLI execution
            ["git", "config", "user.email"], capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        raise RuntimeError(
            "Git user.email not configured. Run: git config --global user.email 'you@example.com'"
        )


def get_git_user_name() -> Optional[str]:
    """Get user name from git config.

    Returns:
        User name from git config, or None if not configured
    """
    try:
        result = subprocess.run(  # nosec B603, B607 - Controlled git CLI execution
            ["git", "config", "user.name"],
            capture_output=True,
            text=True,
            check=True,
            timeout=GIT_COMMAND_TIMEOUT_SECONDS,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        logger.debug(f"Git user.name not configured: {e}")
        return None
    except subprocess.TimeoutExpired:
        logger.warning("Git command timeout when fetching user.name")
        return None
    except FileNotFoundError:
        logger.error("Git not found in PATH")
        return None


def load_developer_mappings() -> dict:
    """Load developer name mappings from config file.

    Returns:
        Dictionary with email_to_name and name_to_canonical mappings
    """
    config_path = Path(__file__).parent.parent.parent / "config" / "developer_names.json"

    with open(config_path) as f:
        config = json.load(f)

    # Build lookup maps
    email_to_canonical = {}
    name_to_canonical = {}

    for dev in config["developers"]:
        canonical = dev["canonical_name"]

        # Map git emails (primary source)
        for git_email in dev.get("git_emails", []):
            email_to_canonical[git_email.lower()] = canonical

        # Map linear emails (many contain email addresses)
        for linear_name in dev.get("linear_names", []):
            if "@" in linear_name:
                email_to_canonical[linear_name.lower()] = canonical

        # Map git names
        for git_name in dev.get("git_names", []):
            name_to_canonical[git_name.lower()] = canonical

    return {"email_to_canonical": email_to_canonical, "name_to_canonical": name_to_canonical}


def detect_developer() -> str:
    """Detect developer canonical name from git configuration.

    Returns:
        Canonical developer name

    Raises:
        RuntimeError: If git is not configured or developer cannot be detected

    Example:
        >>> developer = detect_developer()
        >>> print(developer)
        Chad
    """
    mappings = load_developer_mappings()

    # Try email first (most reliable)
    email = get_git_user_email()
    canonical = mappings["email_to_canonical"].get(email.lower())
    if canonical:
        logger.debug(f"Detected developer from email mapping: {canonical}")
        return canonical

    # Try git name
    git_name = get_git_user_name()
    if git_name:
        canonical = mappings["name_to_canonical"].get(git_name.lower())
        if canonical:
            logger.debug(f"Detected developer from name mapping: {canonical}")
            return canonical

    # Fallback to email username - but validate it first
    if "@" in email:
        fallback = email.split("@")[0]
        # Validate fallback name is reasonable (letters, numbers, underscores, hyphens)
        import re

        if re.match(r"^[a-zA-Z][a-zA-Z0-9_-]+$", fallback):
            logger.warning(
                f"No mapping found in config/developer_names.json for email '{email}' or git name '{git_name}'. "
                f"Using email username as fallback: {fallback}. "
                f"Consider adding this developer to config/developer_names.json for proper mapping."
            )
            return fallback

    # Cannot detect developer - require manual specification
    raise RuntimeError(
        f"Could not auto-detect developer from git config. "
        f"Git email: '{email}', Git name: '{git_name}'. "
        f"Please add this developer to config/developer_names.json or use --developer flag to specify manually."
    )

#!/usr/bin/env python3
"""
Configuration installer for aclarai.

Similar to the prompt installer, this script ensures the user has a
configuration file and can restore defaults when needed.
"""

import logging
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)


def find_project_root() -> Path:
    """Find the project root directory."""
    current = Path.cwd()
    for path in [current] + list(current.parents):
        if (path / "settings").exists() and (path / "shared").exists():
            return path

    # Fallback to current directory
    return current


def install_default_config(force: bool = False) -> bool:
    """
    Install the default configuration file if it doesn't exist.

    Args:
        force: If True, overwrites existing user config

    Returns:
        True if config was installed, False if already exists
    """
    project_root = find_project_root()
    settings_dir = project_root / "settings"
    shared_dir = project_root / "shared" / "aclarai_shared"

    default_config_path = shared_dir / "aclarai.config.default.yaml"
    user_config_path = settings_dir / "aclarai.config.yaml"

    # Check if default config exists
    if not default_config_path.exists():
        logger.error(f"Default configuration file not found at {default_config_path}")
        return False

    # Check if user config already exists
    if user_config_path.exists() and not force:
        logger.info(f"User configuration already exists at {user_config_path}")
        return False

    # Create settings directory if it doesn't exist
    settings_dir.mkdir(parents=True, exist_ok=True)

    # Copy default config to user config
    try:
        shutil.copy2(default_config_path, user_config_path)
        if force:
            logger.info(f"Restored configuration from defaults: {user_config_path}")
        else:
            logger.info(f"Installed configuration file: {user_config_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to install configuration: {e}")
        return False

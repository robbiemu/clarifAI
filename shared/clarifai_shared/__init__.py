"""
Shared utilities and configuration for ClarifAI services.
"""

from .config import ClarifAIConfig, DatabaseConfig, VaultPaths, load_config
from .plugin_interface import Plugin, MarkdownOutput, UnknownFormatError

try:
    from .plugins import ensure_defaults, convert_file_to_markdowns, DefaultPlugin
    from .import_system import (
        Tier1ImportSystem,
        DuplicateDetectionError,
        ImportSystemError,
    )

    __all__ = [
        "ClarifAIConfig",
        "DatabaseConfig",
        "VaultPaths",
        "load_config",
        "Plugin",
        "MarkdownOutput",
        "UnknownFormatError",
        "ensure_defaults",
        "convert_file_to_markdowns",
        "DefaultPlugin",
        "Tier1ImportSystem",
        "DuplicateDetectionError",
        "ImportSystemError",
    ]
except ImportError:
    # LlamaIndex dependencies not available
    __all__ = [
        "ClarifAIConfig",
        "DatabaseConfig",
        "VaultPaths",
        "load_config",
        "Plugin",
        "MarkdownOutput",
        "UnknownFormatError",
    ]

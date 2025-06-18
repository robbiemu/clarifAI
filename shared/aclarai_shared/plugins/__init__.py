"""Plugins package for aclarai format conversion."""

try:
    from .default_plugin import DefaultPlugin
    from .utils import ensure_defaults, convert_file_to_markdowns

    __all__ = ["DefaultPlugin", "ensure_defaults", "convert_file_to_markdowns"]
except ImportError:
    # LlamaIndex not available, provide dummy implementations for testing
    class DefaultPlugin:
        pass

    def ensure_defaults(*args, **kwargs):
        pass

    def convert_file_to_markdowns(*args, **kwargs):
        return []

    __all__ = ["DefaultPlugin", "ensure_defaults", "convert_file_to_markdowns"]

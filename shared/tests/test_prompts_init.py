"""
Tests for prompts module initialization.
"""

import importlib.util
import os

# Load the module directly
module_path = os.path.join(
    os.path.dirname(__file__), "../clarifai_shared/prompts/__init__.py"
)
spec = importlib.util.spec_from_file_location("prompts_init", module_path)
prompts_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prompts_module)


class TestPromptsInit:
    """Test cases for prompts __init__.py module."""

    def test_module_docstring(self):
        """Test that module has expected docstring."""
        assert prompts_module.__doc__ == "Prompt templates for plugin system."

    def test_module_attributes(self):
        """Test basic module attributes."""
        # Should have basic Python module attributes
        assert hasattr(prompts_module, "__doc__")

    def test_module_is_module(self):
        """Test that we loaded a valid module."""
        import types

        assert isinstance(prompts_module, types.ModuleType)

    def test_module_name(self):
        """Test module has correct name."""
        assert prompts_module.__name__ == "prompts_init"

    def test_module_no_exports(self):
        """Test that module doesn't export unexpected symbols."""
        # Should be minimal - just the docstring and standard module attributes
        actual_attrs = set(dir(prompts_module))

        # Only check that we don't have unexpected public attributes
        public_attrs = {attr for attr in actual_attrs if not attr.startswith("_")}
        assert len(public_attrs) == 0  # Should only have private/dunder attributes

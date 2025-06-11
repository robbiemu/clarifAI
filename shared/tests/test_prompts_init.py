"""
Tests for prompts module initialization.
"""

import types

import clarifai_shared.prompts as prompts_module


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
        assert isinstance(prompts_module, types.ModuleType)

    def test_module_name(self):
        """Test module has correct name."""
        assert prompts_module.__name__ == "clarifai_shared.prompts"

    def test_module_no_exports(self):
        """Test that module doesn't export unexpected symbols."""
        # Should be minimal - just the docstring and standard module attributes
        actual_attrs = set(dir(prompts_module))

        # Only check that we don't have unexpected public attributes
        public_attrs = {attr for attr in actual_attrs if not attr.startswith("_")}
        assert len(public_attrs) == 0  # Should only have private/dunder attributes

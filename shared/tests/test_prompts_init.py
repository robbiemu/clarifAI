"""
Tests for prompts module initialization.
"""

import os


class TestPromptsInit:
    """Test cases for prompts __init__.py module."""

    def test_prompts_init_file_exists(self):
        """Test that the prompts __init__.py file exists."""
        init_path = os.path.join(
            os.path.dirname(__file__), "../aclarai_shared/prompts/__init__.py"
        )
        assert os.path.exists(init_path)

    def test_prompts_init_file_structure(self):
        """Test that the prompts __init__.py file has expected structure."""
        init_path = os.path.join(
            os.path.dirname(__file__), "../aclarai_shared/prompts/__init__.py"
        )
        with open(init_path, "r") as f:
            content = f.read()
        # Check for expected docstring
        assert "Prompt templates for plugin system." in content
        # Check that it's a minimal module (no exports)
        assert "__all__" not in content or "__all__ = []" in content

    def test_prompts_directory_structure(self):
        """Test that the prompts directory exists and has expected structure."""
        prompts_dir = os.path.join(
            os.path.dirname(__file__), "../aclarai_shared/prompts"
        )
        assert os.path.exists(prompts_dir)
        assert os.path.isdir(prompts_dir)
        # Check that __init__.py exists
        init_file = os.path.join(prompts_dir, "__init__.py")
        assert os.path.exists(init_file)

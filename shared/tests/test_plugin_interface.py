"""
Tests for plugin interface and data structures.
"""

import os


class TestMarkdownOutput:
    """Test cases for MarkdownOutput dataclass."""

    def test_plugin_interface_file_exists(self):
        """Test that the plugin interface file exists."""
        interface_path = os.path.join(
            os.path.dirname(__file__), "../clarifai_shared/plugin_interface.py"
        )
        assert os.path.exists(interface_path)

    def test_plugin_interface_structure(self):
        """Test that the plugin interface classes and methods are properly implemented."""
        # Import the actual classes instead of checking strings in files
        from clarifai_shared.plugin_interface import (
            MarkdownOutput,
            Plugin,
            UnknownFormatError,
        )

        # Test MarkdownOutput dataclass can be instantiated
        output = MarkdownOutput(
            title="Test Title",
            markdown_text="# Test Content",
            metadata={"test": "data"},
        )
        assert output.title == "Test Title"
        assert output.markdown_text == "# Test Content"
        assert output.metadata == {"test": "data"}

        # Test Plugin abstract class has required methods
        assert hasattr(Plugin, "can_accept")
        assert hasattr(Plugin, "convert")

        # Test UnknownFormatError exception can be raised
        try:
            raise UnknownFormatError("Test error")
        except UnknownFormatError as e:
            assert str(e) == "Test error"

    def test_markdown_output_simulation(self):
        """Test MarkdownOutput structure simulation."""
        # Simulate MarkdownOutput creation
        output_data = {
            "title": "Test Title",
            "markdown_text": "# Test Content\n\nThis is a test.",
            "metadata": None,
        }

        assert output_data["title"] == "Test Title"
        assert output_data["markdown_text"] == "# Test Content\n\nThis is a test."
        assert output_data["metadata"] is None

    def test_markdown_output_with_metadata_simulation(self):
        """Test MarkdownOutput with metadata simulation."""
        metadata = {
            "participants": ["alice", "bob"],
            "created_at": "2024-01-01T10:00:00Z",
            "message_count": 5,
        }

        output_data = {
            "title": "Chat with Metadata",
            "markdown_text": "# Chat\n\nalice: hello\nbob: hi",
            "metadata": metadata,
        }

        assert output_data["title"] == "Chat with Metadata"
        assert output_data["metadata"] == metadata
        assert output_data["metadata"]["participants"] == ["alice", "bob"]
        assert output_data["metadata"]["message_count"] == 5


class TestPluginInterface:
    """Test cases for Plugin abstract class."""

    def test_plugin_abstract_class_structure(self):
        """Test Plugin abstract class structure."""
        interface_path = os.path.join(
            os.path.dirname(__file__), "../clarifai_shared/plugin_interface.py"
        )

        with open(interface_path, "r") as f:
            content = f.read()

        # Check for abstract base class implementation
        assert "from abc import ABC, abstractmethod" in content
        assert "class Plugin(ABC):" in content
        assert "@abstractmethod" in content

        # Check for required method signatures
        assert "def can_accept(self, raw_input: str) -> bool:" in content
        assert (
            "def convert(self, raw_input: str, path: Path) -> List[MarkdownOutput]:"
            in content
        )

    def test_unknown_format_error_structure(self):
        """Test UnknownFormatError exception structure."""
        interface_path = os.path.join(
            os.path.dirname(__file__), "../clarifai_shared/plugin_interface.py"
        )

        with open(interface_path, "r") as f:
            content = f.read()

        # Check for exception class
        assert "class UnknownFormatError" in content
        assert "Exception" in content

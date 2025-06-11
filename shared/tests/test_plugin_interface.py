"""
Tests for plugin interface and data structures.
"""

import pytest
import importlib.util
import os
from pathlib import Path

# Load the module directly without triggering __init__.py imports
module_path = os.path.join(os.path.dirname(__file__), '../clarifai_shared/plugin_interface.py')
spec = importlib.util.spec_from_file_location("plugin_interface", module_path)
plugin_interface = importlib.util.module_from_spec(spec)
spec.loader.exec_module(plugin_interface)

MarkdownOutput = plugin_interface.MarkdownOutput
Plugin = plugin_interface.Plugin
UnknownFormatError = plugin_interface.UnknownFormatError


class TestMarkdownOutput:
    """Test cases for MarkdownOutput dataclass."""

    def test_markdown_output_basic_creation(self):
        """Test basic MarkdownOutput creation."""
        output = MarkdownOutput(
            title="Test Title",
            markdown_text="# Test Content\n\nThis is a test."
        )
        
        assert output.title == "Test Title"
        assert output.markdown_text == "# Test Content\n\nThis is a test."
        assert output.metadata is None

    def test_markdown_output_with_metadata(self):
        """Test MarkdownOutput with metadata."""
        metadata = {
            "participants": ["alice", "bob"],
            "created_at": "2024-01-01T10:00:00Z",
            "message_count": 5
        }
        
        output = MarkdownOutput(
            title="Chat with Metadata",
            markdown_text="# Chat\n\nalice: hello\nbob: hi",
            metadata=metadata
        )
        
        assert output.title == "Chat with Metadata"
        assert output.metadata == metadata
        assert output.metadata["participants"] == ["alice", "bob"]
        assert output.metadata["message_count"] == 5

    def test_markdown_output_equality(self):
        """Test MarkdownOutput equality."""
        output1 = MarkdownOutput(
            title="Same Title",
            markdown_text="Same content",
            metadata={"key": "value"}
        )
        output2 = MarkdownOutput(
            title="Same Title",
            markdown_text="Same content",
            metadata={"key": "value"}
        )
        output3 = MarkdownOutput(
            title="Different Title",
            markdown_text="Same content",
            metadata={"key": "value"}
        )
        
        assert output1 == output2
        assert output1 != output3

    def test_markdown_output_empty_metadata(self):
        """Test MarkdownOutput with empty metadata."""
        output = MarkdownOutput(
            title="Empty Meta",
            markdown_text="Content",
            metadata={}
        )
        
        assert output.metadata == {}
        assert len(output.metadata) == 0


class TestPlugin:
    """Test cases for Plugin abstract base class."""

    def test_plugin_is_abstract(self):
        """Test that Plugin cannot be instantiated directly."""
        with pytest.raises(TypeError):
            Plugin()

    def test_plugin_subclass_missing_methods(self):
        """Test that Plugin subclass must implement abstract methods."""
        class IncompletePlugin(Plugin):
            # Missing both abstract methods
            pass
        
        with pytest.raises(TypeError):
            IncompletePlugin()

    def test_plugin_subclass_missing_one_method(self):
        """Test that Plugin subclass must implement both abstract methods."""
        class PartialPlugin(Plugin):
            def can_accept(self, raw_input: str) -> bool:
                return True
            # Missing convert method
        
        with pytest.raises(TypeError):
            PartialPlugin()

    def test_plugin_subclass_complete(self):
        """Test that Plugin subclass with all methods can be instantiated."""
        class CompletePlugin(Plugin):
            def can_accept(self, raw_input: str) -> bool:
                return True
                
            def convert(self, raw_input: str, path: Path) -> list:
                return [MarkdownOutput(title="Test", markdown_text="Content")]
        
        # Should not raise an exception
        plugin = CompletePlugin()
        assert isinstance(plugin, Plugin)
        assert plugin.can_accept("test") is True
        
        result = plugin.convert("test", Path("/test/path"))
        assert len(result) == 1
        assert isinstance(result[0], MarkdownOutput)

    def test_plugin_subclass_methods_callable(self):
        """Test that Plugin subclass methods work correctly."""
        class TestPlugin(Plugin):
            def can_accept(self, raw_input: str) -> bool:
                return "test" in raw_input.lower()
                
            def convert(self, raw_input: str, path: Path) -> list:
                return [MarkdownOutput(
                    title=f"Converted from {path.name}",
                    markdown_text=f"# Converted\n\n{raw_input}"
                )]
        
        plugin = TestPlugin()
        
        # Test can_accept
        assert plugin.can_accept("This is a test") is True
        assert plugin.can_accept("No match here") is False
        
        # Test convert
        test_path = Path("/test/file.txt")
        result = plugin.convert("test content", test_path)
        
        assert len(result) == 1
        output = result[0]
        assert output.title == "Converted from file.txt"
        assert "test content" in output.markdown_text


class TestUnknownFormatError:
    """Test cases for UnknownFormatError exception."""

    def test_unknown_format_error_basic(self):
        """Test basic UnknownFormatError creation and raising."""
        with pytest.raises(UnknownFormatError):
            raise UnknownFormatError()

    def test_unknown_format_error_with_message(self):
        """Test UnknownFormatError with custom message."""
        error_message = "No plugin found for format XYZ"
        
        with pytest.raises(UnknownFormatError, match=error_message):
            raise UnknownFormatError(error_message)

    def test_unknown_format_error_inheritance(self):
        """Test that UnknownFormatError inherits from Exception."""
        error = UnknownFormatError("test message")
        assert isinstance(error, Exception)

    def test_unknown_format_error_str_representation(self):
        """Test string representation of UnknownFormatError."""
        message = "Test error message"
        error = UnknownFormatError(message)
        assert str(error) == message

    def test_unknown_format_error_empty_message(self):
        """Test UnknownFormatError with empty message."""
        error = UnknownFormatError("")
        assert str(error) == ""


class TestModuleStructure:
    """Test module-level structure and imports."""

    def test_module_exports(self):
        """Test that module exports expected classes."""
        assert hasattr(plugin_interface, 'MarkdownOutput')
        assert hasattr(plugin_interface, 'Plugin')
        assert hasattr(plugin_interface, 'UnknownFormatError')

    def test_class_types(self):
        """Test that exported classes have correct types."""
        assert isinstance(MarkdownOutput, type)
        assert isinstance(Plugin, type)
        assert isinstance(UnknownFormatError, type)
        
        # Test inheritance
        assert issubclass(UnknownFormatError, Exception)
        from abc import ABC
        assert issubclass(Plugin, ABC)
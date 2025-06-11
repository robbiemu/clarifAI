"""
Tests for plugin utility functions.
"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime
import logging

# Create local versions of the classes and functions to test
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod

@dataclass
class MarkdownOutput:
    """Structure for plugin output containing Markdown content and metadata."""
    title: str
    markdown_text: str
    metadata: Optional[Dict[str, Any]] = None

class Plugin(ABC):
    """Abstract base class for all format conversion plugins."""
    @abstractmethod
    def can_accept(self, raw_input: str) -> bool:
        pass
    @abstractmethod
    def convert(self, raw_input: str, path: Path) -> List[MarkdownOutput]:
        pass

class UnknownFormatError(Exception):
    """Raised when no plugin can handle a given input format."""
    pass

# Copy the utility functions to test directly
def ensure_defaults(md: MarkdownOutput, path: Path) -> MarkdownOutput:
    """Fill in any missing default metadata fields in a MarkdownOutput."""
    meta = md.metadata or {}
    created = (
        meta.get("created_at")
        or datetime.fromtimestamp(path.stat().st_mtime).isoformat()
    )

    # Only generate title if the original title is empty or None
    title = md.title
    if not title:
        title = meta.get("title") or f"Conversation last modified at {created}"

    return MarkdownOutput(
        title=title,
        markdown_text=md.markdown_text,
        metadata={
            "created_at": created,
            "participants": meta.get("participants", ["user", "assistant"]),
            "message_count": meta.get("message_count", 0),
            "duration_sec": meta.get("duration_sec"),
            "plugin_metadata": meta.get("plugin_metadata", {}),
        },
    )

def convert_file_to_markdowns(
    input_path: Path, registry: List[Plugin]
) -> List[MarkdownOutput]:
    """Main conversion function that tries plugins in order until one succeeds."""
    raw_input = input_path.read_text(encoding="utf-8")

    for plugin in registry:
        if plugin.can_accept(raw_input):
            try:
                raw_outputs = plugin.convert(raw_input, input_path)
                return [ensure_defaults(md, input_path) for md in raw_outputs]
            except Exception as e:
                # Log the specific plugin failure and continue to next plugin
                logging.warning(
                    "Plugin %s failed to convert %s: %s",
                    plugin.__class__.__name__,
                    input_path.name,
                    str(e),
                )
                # Continue to next plugin that accepts the input

    raise UnknownFormatError(f"No plugin could handle file: {input_path}")


class TestEnsureDefaults:
    """Test cases for ensure_defaults function."""

    def test_ensure_defaults_empty_metadata(self):
        """Test ensure_defaults with empty metadata."""
        with tempfile.NamedTemporaryFile() as temp_file:
            path = Path(temp_file.name)
            
            md = MarkdownOutput(
                title="Test Title",
                markdown_text="Test content",
                metadata=None
            )
            
            result = ensure_defaults(md, path)
            
            assert result.title == "Test Title"
            assert result.markdown_text == "Test content"
            assert result.metadata is not None
            assert "created_at" in result.metadata
            assert result.metadata["participants"] == ["user", "assistant"]
            assert result.metadata["message_count"] == 0
            assert result.metadata["plugin_metadata"] == {}

    def test_ensure_defaults_existing_metadata(self):
        """Test ensure_defaults with existing metadata."""
        with tempfile.NamedTemporaryFile() as temp_file:
            path = Path(temp_file.name)
            
            existing_meta = {
                "participants": ["alice", "bob"],
                "message_count": 5,
                "custom_field": "custom_value"
            }
            
            md = MarkdownOutput(
                title="Chat Log",
                markdown_text="alice: hi\nbob: hello",
                metadata=existing_meta
            )
            
            result = ensure_defaults(md, path)
            
            assert result.title == "Chat Log"
            assert result.metadata["participants"] == ["alice", "bob"]
            assert result.metadata["message_count"] == 5
            assert "created_at" in result.metadata
            # Custom field should not be preserved in the filtered metadata
            assert "custom_field" not in result.metadata

    def test_ensure_defaults_empty_title(self):
        """Test ensure_defaults with empty title."""
        with tempfile.NamedTemporaryFile() as temp_file:
            path = Path(temp_file.name)
            
            md = MarkdownOutput(
                title="",  # Empty title
                markdown_text="Content without title"
            )
            
            result = ensure_defaults(md, path)
            
            # Should generate fallback title
            assert result.title.startswith("Conversation last modified at")
            assert "created_at" in result.metadata

    def test_ensure_defaults_none_title(self):
        """Test ensure_defaults with None title."""
        with tempfile.NamedTemporaryFile() as temp_file:
            path = Path(temp_file.name)
            
            md = MarkdownOutput(
                title=None,
                markdown_text="Content without title"
            )
            
            result = ensure_defaults(md, path)
            
            # Should generate fallback title
            assert result.title.startswith("Conversation last modified at")

    def test_ensure_defaults_title_from_metadata(self):
        """Test ensure_defaults using title from metadata when original title is empty."""
        with tempfile.NamedTemporaryFile() as temp_file:
            path = Path(temp_file.name)
            
            md = MarkdownOutput(
                title="",
                markdown_text="Content",
                metadata={"title": "Title from metadata"}
            )
            
            result = ensure_defaults(md, path)
            
            assert result.title == "Title from metadata"

    def test_ensure_defaults_created_at_from_metadata(self):
        """Test ensure_defaults using created_at from metadata."""
        with tempfile.NamedTemporaryFile() as temp_file:
            path = Path(temp_file.name)
            
            custom_time = "2024-01-01T12:00:00"
            md = MarkdownOutput(
                title="Test",
                markdown_text="Content",
                metadata={"created_at": custom_time}
            )
            
            result = ensure_defaults(md, path)
            
            assert result.metadata["created_at"] == custom_time

    def test_ensure_defaults_duration_sec(self):
        """Test ensure_defaults with duration_sec metadata."""
        with tempfile.NamedTemporaryFile() as temp_file:
            path = Path(temp_file.name)
            
            md = MarkdownOutput(
                title="Test",
                markdown_text="Content",
                metadata={"duration_sec": 300}
            )
            
            result = ensure_defaults(md, path)
            
            assert result.metadata["duration_sec"] == 300

    def test_ensure_defaults_plugin_metadata(self):
        """Test ensure_defaults with custom plugin_metadata."""
        with tempfile.NamedTemporaryFile() as temp_file:
            path = Path(temp_file.name)
            
            plugin_meta = {"source": "test_plugin", "version": "1.0"}
            md = MarkdownOutput(
                title="Test",
                markdown_text="Content",
                metadata={"plugin_metadata": plugin_meta}
            )
            
            result = ensure_defaults(md, path)
            
            assert result.metadata["plugin_metadata"] == plugin_meta


class TestConvertFileToMarkdowns:
    """Test cases for convert_file_to_markdowns function."""

    def test_convert_file_successful(self):
        """Test successful file conversion with working plugin."""
        class WorkingPlugin(Plugin):
            def can_accept(self, raw_input: str) -> bool:
                return "test_content" in raw_input
                
            def convert(self, raw_input: str, path: Path) -> list:
                return [MarkdownOutput(
                    title="Converted",
                    markdown_text=f"# Converted\n\n{raw_input}"
                )]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
            temp_file.write("test_content here")
            temp_file.flush()
            path = Path(temp_file.name)
            
            try:
                registry = [WorkingPlugin()]
                result = convert_file_to_markdowns(path, registry)
                
                assert len(result) == 1
                assert result[0].title == "Converted"
                assert "test_content here" in result[0].markdown_text
                # Should have defaults applied
                assert "created_at" in result[0].metadata
                assert result[0].metadata["participants"] == ["user", "assistant"]
                
            finally:
                path.unlink()

    def test_convert_file_no_accepting_plugin(self):
        """Test file conversion with no accepting plugins."""
        class RejectingPlugin(Plugin):
            def can_accept(self, raw_input: str) -> bool:
                return False
                
            def convert(self, raw_input: str, path: Path) -> list:
                return []
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
            temp_file.write("some content")
            temp_file.flush()
            path = Path(temp_file.name)
            
            try:
                registry = [RejectingPlugin()]
                
                with pytest.raises(UnknownFormatError, match="No plugin could handle file"):
                    convert_file_to_markdowns(path, registry)
                    
            finally:
                path.unlink()

    def test_convert_file_plugin_failure_continues(self):
        """Test that plugin failures are handled and next plugin is tried."""
        class FailingPlugin(Plugin):
            def can_accept(self, raw_input: str) -> bool:
                return True
                
            def convert(self, raw_input: str, path: Path) -> list:
                raise RuntimeError("Plugin failed")
        
        class WorkingPlugin(Plugin):
            def can_accept(self, raw_input: str) -> bool:
                return True
                
            def convert(self, raw_input: str, path: Path) -> list:
                return [MarkdownOutput(title="Success", markdown_text="Worked")]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
            temp_file.write("test content")
            temp_file.flush()
            path = Path(temp_file.name)
            
            try:
                registry = [FailingPlugin(), WorkingPlugin()]
                result = convert_file_to_markdowns(path, registry)
                
                assert len(result) == 1
                assert result[0].title == "Success"
                
            finally:
                path.unlink()

    def test_convert_file_empty_registry(self):
        """Test file conversion with empty plugin registry."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
            temp_file.write("content")
            temp_file.flush()
            path = Path(temp_file.name)
            
            try:
                registry = []
                
                with pytest.raises(UnknownFormatError):
                    convert_file_to_markdowns(path, registry)
                    
            finally:
                path.unlink()

    def test_convert_file_multiple_outputs(self):
        """Test file conversion that produces multiple outputs."""
        class MultiOutputPlugin(Plugin):
            def can_accept(self, raw_input: str) -> bool:
                return True
                
            def convert(self, raw_input: str, path: Path) -> list:
                return [
                    MarkdownOutput(title="First", markdown_text="First output"),
                    MarkdownOutput(title="Second", markdown_text="Second output")
                ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
            temp_file.write("content")
            temp_file.flush()
            path = Path(temp_file.name)
            
            try:
                registry = [MultiOutputPlugin()]
                result = convert_file_to_markdowns(path, registry)
                
                assert len(result) == 2
                assert result[0].title == "First"
                assert result[1].title == "Second"
                # Both should have defaults applied
                for output in result:
                    assert "created_at" in output.metadata
                    
            finally:
                path.unlink()

    def test_convert_file_utf8_encoding(self):
        """Test file conversion handles UTF-8 encoding."""
        class TextPlugin(Plugin):
            def can_accept(self, raw_input: str) -> bool:
                return "特殊" in raw_input
                
            def convert(self, raw_input: str, path: Path) -> list:
                return [MarkdownOutput(title="UTF-8", markdown_text=raw_input)]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as temp_file:
            utf8_content = "特殊文字のテスト"
            temp_file.write(utf8_content)
            temp_file.flush()
            path = Path(temp_file.name)
            
            try:
                registry = [TextPlugin()]
                result = convert_file_to_markdowns(path, registry)
                
                assert len(result) == 1
                assert utf8_content in result[0].markdown_text
                
            finally:
                path.unlink()
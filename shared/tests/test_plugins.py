"""
Tests for the plugin system infrastructure.
"""

import tempfile
from pathlib import Path
from datetime import datetime

import pytest

from clarifai_shared import (
    Plugin,
    MarkdownOutput,
    ensure_defaults,
    convert_file_to_markdowns,
    UnknownFormatError,
)


class MockPlugin(Plugin):
    """Simple mock plugin for testing."""
    
    def __init__(self, accepts=True, output_count=1):
        self.accepts = accepts
        self.output_count = output_count
    
    def can_accept(self, raw_input: str) -> bool:
        return self.accepts
    
    def convert(self, raw_input: str, path: Path) -> list[MarkdownOutput]:
        outputs = []
        for i in range(self.output_count):
            outputs.append(MarkdownOutput(
                title=f"Test Conversation {i+1}",
                markdown_text="speaker1: Hello\nspeaker2: Hi there",
                metadata={
                    "participants": ["speaker1", "speaker2"],
                    "message_count": 2,
                    "plugin_metadata": {"source": "mock"}
                }
            ))
        return outputs


class FailingPlugin(Plugin):
    """Plugin that fails during conversion for testing error handling."""
    
    def can_accept(self, raw_input: str) -> bool:
        return True
    
    def convert(self, raw_input: str, path: Path) -> list[MarkdownOutput]:
        raise Exception("Conversion failed")


def test_markdown_output_creation():
    """Test MarkdownOutput dataclass creation."""
    md = MarkdownOutput(
        title="Test Conversation",
        markdown_text="speaker: Hello world",
        metadata={"test": "value"}
    )
    
    assert md.title == "Test Conversation"
    assert md.markdown_text == "speaker: Hello world"
    assert md.metadata == {"test": "value"}


def test_ensure_defaults_with_complete_metadata():
    """Test ensure_defaults when all metadata is provided."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("test content")
        temp_path = Path(f.name)
    
    try:
        md = MarkdownOutput(
            title="Custom Title",
            markdown_text="content",
            metadata={
                "created_at": "2023-01-01T00:00:00Z",
                "participants": ["alice", "bob"],
                "message_count": 5,
                "duration_sec": 300,
                "plugin_metadata": {"source": "test"}
            }
        )
        
        result = ensure_defaults(md, temp_path)
        
        assert result.title == "Custom Title"
        assert result.markdown_text == "content"
        assert result.metadata["created_at"] == "2023-01-01T00:00:00Z"
        assert result.metadata["participants"] == ["alice", "bob"]
        assert result.metadata["message_count"] == 5
        assert result.metadata["duration_sec"] == 300
        assert result.metadata["plugin_metadata"] == {"source": "test"}
    finally:
        temp_path.unlink()


def test_ensure_defaults_with_missing_metadata():
    """Test ensure_defaults fills in missing metadata."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("test content")
        temp_path = Path(f.name)
    
    try:
        md = MarkdownOutput(
            title="",  # Empty title
            markdown_text="content",
            metadata={}  # Empty metadata
        )
        
        result = ensure_defaults(md, temp_path)
        
        # Title should be generated from created_at
        assert "Conversation last modified at" in result.title
        
        # Check all default fields are present
        assert "created_at" in result.metadata
        assert result.metadata["participants"] == ["user", "assistant"]
        assert result.metadata["message_count"] == 0
        assert result.metadata["duration_sec"] is None
        assert result.metadata["plugin_metadata"] == {}
        
        # Verify created_at is a valid ISO timestamp
        created_at = result.metadata["created_at"]
        datetime.fromisoformat(created_at.replace('Z', '+00:00'))
    finally:
        temp_path.unlink()


def test_ensure_defaults_with_no_metadata():
    """Test ensure_defaults when metadata is None."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("test content")
        temp_path = Path(f.name)
    
    try:
        md = MarkdownOutput(
            title="Test",
            markdown_text="content",
            metadata=None
        )
        
        result = ensure_defaults(md, temp_path)
        
        assert result.title == "Test"
        assert result.metadata is not None
        assert result.metadata["participants"] == ["user", "assistant"]
        assert result.metadata["message_count"] == 0
    finally:
        temp_path.unlink()


def test_convert_file_to_markdowns_success():
    """Test successful file conversion with plugin."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("speaker1: Hello\nspeaker2: Hi")
        temp_path = Path(f.name)
    
    try:
        plugin = MockPlugin(accepts=True, output_count=1)
        registry = [plugin]
        
        results = convert_file_to_markdowns(temp_path, registry)
        
        assert len(results) == 1
        assert results[0].title == "Test Conversation 1"
        assert "created_at" in results[0].metadata
        assert results[0].metadata["participants"] == ["speaker1", "speaker2"]
    finally:
        temp_path.unlink()


def test_convert_file_to_markdowns_multiple_outputs():
    """Test file conversion that produces multiple conversations."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("test content")
        temp_path = Path(f.name)
    
    try:
        plugin = MockPlugin(accepts=True, output_count=3)
        registry = [plugin]
        
        results = convert_file_to_markdowns(temp_path, registry)
        
        assert len(results) == 3
        for i, result in enumerate(results):
            assert result.title == f"Test Conversation {i+1}"
            assert "created_at" in result.metadata
    finally:
        temp_path.unlink()


def test_convert_file_to_markdowns_plugin_order():
    """Test that plugins are tried in order until one succeeds."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("test content")
        temp_path = Path(f.name)
    
    try:
        plugin1 = MockPlugin(accepts=False)  # Rejects input
        plugin2 = MockPlugin(accepts=True)   # Accepts input
        plugin3 = MockPlugin(accepts=True)   # Should not be reached
        
        registry = [plugin1, plugin2, plugin3]
        
        results = convert_file_to_markdowns(temp_path, registry)
        
        assert len(results) == 1
        assert results[0].title == "Test Conversation 1"
    finally:
        temp_path.unlink()


def test_convert_file_to_markdowns_plugin_failure_recovery():
    """Test that conversion continues if a plugin fails."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("test content")
        temp_path = Path(f.name)
    
    try:
        plugin1 = FailingPlugin()             # Accepts but fails
        plugin2 = MockPlugin(accepts=True)    # Should handle it
        
        registry = [plugin1, plugin2]
        
        results = convert_file_to_markdowns(temp_path, registry)
        
        assert len(results) == 1
        assert results[0].title == "Test Conversation 1"
    finally:
        temp_path.unlink()


def test_convert_file_to_markdowns_no_accepting_plugin():
    """Test error when no plugin can handle the input."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("test content")
        temp_path = Path(f.name)
    
    try:
        plugin1 = MockPlugin(accepts=False)
        plugin2 = MockPlugin(accepts=False)
        
        registry = [plugin1, plugin2]
        
        with pytest.raises(UnknownFormatError) as exc_info:
            convert_file_to_markdowns(temp_path, registry)
        
        assert str(temp_path) in str(exc_info.value)
    finally:
        temp_path.unlink()


def test_convert_file_to_markdowns_empty_registry():
    """Test error when plugin registry is empty."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("test content")
        temp_path = Path(f.name)
    
    try:
        registry = []
        
        with pytest.raises(UnknownFormatError):
            convert_file_to_markdowns(temp_path, registry)
    finally:
        temp_path.unlink()


def test_convert_file_to_markdowns_utf8_encoding():
    """Test that files are read with UTF-8 encoding."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt', encoding='utf-8') as f:
        f.write("speaker: Héllo wörld 🌍")
        temp_path = Path(f.name)
    
    try:
        plugin = MockPlugin(accepts=True)
        registry = [plugin]
        
        results = convert_file_to_markdowns(temp_path, registry)
        
        assert len(results) == 1
        # The plugin should have received the UTF-8 content
    finally:
        temp_path.unlink()
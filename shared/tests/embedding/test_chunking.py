"""
Tests for aclarai embedding chunking functionality.
These tests verify the UtteranceChunker implementation following the
specifications from docs/arch/on-sentence_splitting.md
"""

import pytest
from aclarai_shared.config import EmbeddingConfig, aclaraiConfig
from aclarai_shared.embedding.chunking import ChunkMetadata, UtteranceChunker


@pytest.fixture
def mock_config():
    """Create a mock configuration for testing."""
    config = aclaraiConfig()
    config.embedding = EmbeddingConfig(
        chunk_size=300,
        chunk_overlap=30,
        merge_colon_endings=True,
        merge_short_prefixes=True,
        min_chunk_tokens=5,
    )
    return config


@pytest.fixture
def chunker(mock_config):
    """Create a chunker instance for testing."""
    return UtteranceChunker(mock_config)


def test_chunker_initialization(mock_config):
    """Test that chunker initializes correctly with configuration."""
    chunker = UtteranceChunker(mock_config)
    assert chunker.config == mock_config
    assert chunker.splitter is not None


def test_parse_tier1_blocks_basic(chunker):
    """Test parsing basic Tier 1 Markdown format."""
    tier1_content = """
<!-- aclarai:title=Test Conversation -->
<!-- aclarai:created_at=2024-01-01T10:00:00Z -->
Alice: Hello, how are you doing today?
<!-- aclarai:id=blk_abc123 ver=1 -->
^blk_abc123
Bob: I'm doing great, thanks for asking!
<!-- aclarai:id=blk_def456 ver=1 -->
^blk_def456
"""
    blocks = chunker._parse_tier1_blocks(tier1_content)
    assert len(blocks) == 2
    # Check first block
    assert blocks[0]["aclarai_id"] == "blk_abc123"
    assert blocks[0]["speaker"] == "Alice"
    assert blocks[0]["text"] == "Hello, how are you doing today?"
    # Check second block
    assert blocks[1]["aclarai_id"] == "blk_def456"
    assert blocks[1]["speaker"] == "Bob"
    assert blocks[1]["text"] == "I'm doing great, thanks for asking!"


def test_parse_tier1_blocks_multiline(chunker):
    """Test parsing blocks with multiline utterances."""
    tier1_content = """
Alice: This is a longer message that spans
multiple lines and should be combined together.
<!-- aclarai:id=blk_xyz789 ver=1 -->
^blk_xyz789
"""
    blocks = chunker._parse_tier1_blocks(tier1_content)
    assert len(blocks) == 1
    assert blocks[0]["aclarai_id"] == "blk_xyz789"
    assert blocks[0]["speaker"] == "Alice"
    assert "multiple lines and should be combined" in blocks[0]["text"]


def test_chunk_utterance_block_simple(chunker):
    """Test chunking a simple utterance block."""
    text = "This is a simple utterance that should be chunked."
    aclarai_block_id = "blk_test123"
    chunks = chunker.chunk_utterance_block(text, aclarai_block_id)
    assert len(chunks) >= 1
    assert all(isinstance(chunk, ChunkMetadata) for chunk in chunks)
    assert all(chunk.aclarai_block_id == aclarai_block_id for chunk in chunks)
    assert all(chunk.original_text == text for chunk in chunks)
    # Check chunk indices are sequential
    for i, chunk in enumerate(chunks):
        assert chunk.chunk_index == i


def test_chunk_utterance_block_long_text(chunker):
    """Test chunking a long text that requires multiple chunks."""
    # Create a long text that will exceed the chunk size
    long_text = " ".join(
        [f"Sentence {i} with some content to make it longer." for i in range(50)]
    )
    aclarai_block_id = "blk_long123"
    chunks = chunker.chunk_utterance_block(long_text, aclarai_block_id)
    # Should create multiple chunks
    assert len(chunks) > 1
    # All chunks should have the same metadata structure
    for chunk in chunks:
        assert chunk.aclarai_block_id == aclarai_block_id
        assert chunk.original_text == long_text
        assert len(chunk.text) > 0


def test_postprocessing_merge_colon_endings(chunker):
    """Test that colon-ended lead-ins are merged with continuations."""
    # Mock the base chunks to simulate colon-ending scenario
    from aclarai_shared.embedding.chunking import TextNode

    base_chunks = [
        TextNode(text="In the example we see:", metadata={}),
        TextNode(text="the result is successful", metadata={}),
    ]
    processed = chunker._apply_postprocessing_rules(base_chunks)
    # Should merge into one chunk
    assert len(processed) == 1
    assert "In the example we see: the result is successful" in processed[0].text


def test_postprocessing_merge_short_prefixes(chunker):
    """Test that short prefixes are merged with next chunks."""
    from aclarai_shared.embedding.chunking import TextNode

    base_chunks = [
        TextNode(text="Example:", metadata={}),  # Short prefix
        TextNode(text="This is the full explanation that follows.", metadata={}),
    ]
    processed = chunker._apply_postprocessing_rules(base_chunks)
    # Should merge into one chunk
    assert len(processed) == 1
    assert "Example: This is the full explanation" in processed[0].text


def test_count_tokens(chunker):
    """Test the token counting utility function."""
    assert chunker._count_tokens("hello world") == 2
    assert chunker._count_tokens("this is a test sentence") == 5
    assert chunker._count_tokens("") == 0
    assert chunker._count_tokens("single") == 1


def test_chunk_tier1_blocks_integration(chunker):
    """Test the complete tier1 blocks chunking workflow."""
    tier1_content = """
<!-- aclarai:title=Test Integration -->
Alice: This is a test message for integration testing.
<!-- aclarai:id=blk_int001 ver=1 -->
^blk_int001
Bob: And this is another message to verify the workflow.
<!-- aclarai:id=blk_int002 ver=1 -->
^blk_int002
"""
    chunks = chunker.chunk_tier1_blocks(tier1_content)
    # Should have chunks from both blocks
    assert len(chunks) >= 2
    # Check that we have chunks from both block IDs
    block_ids = {chunk.aclarai_block_id for chunk in chunks}
    assert "blk_int001" in block_ids
    assert "blk_int002" in block_ids
    # All chunks should have valid metadata
    for chunk in chunks:
        assert chunk.aclarai_block_id.startswith("blk_")
        assert chunk.chunk_index >= 0
        assert len(chunk.text) > 0
        assert len(chunk.original_text) > 0


def test_chunk_tier1_blocks_empty_content(chunker):
    """Test chunking empty or invalid content."""
    # Empty content
    chunks = chunker.chunk_tier1_blocks("")
    assert len(chunks) == 0
    # Content with no valid blocks
    invalid_content = """
    This is just some text without proper formatting.
    No aclarai:id blocks here.
    """
    chunks = chunker.chunk_tier1_blocks(invalid_content)
    assert len(chunks) == 0


def test_chunker_with_default_config():
    """Test chunker initialization with default config loading."""
    mock_config = aclaraiConfig()
    mock_config.embedding = EmbeddingConfig()
    chunker = UtteranceChunker(mock_config)  # Pass config explicitly
    assert chunker.config == mock_config


def test_parse_tier1_blocks_edge_cases(chunker):
    """Test parsing edge cases in Tier 1 content."""
    # Block without final anchor
    content_no_anchor = """
Alice: Message without anchor
<!-- aclarai:id=blk_noanchor ver=1 -->
"""
    blocks = chunker._parse_tier1_blocks(content_no_anchor)
    assert len(blocks) == 1
    assert blocks[0]["aclarai_id"] == "blk_noanchor"
    # Block with speaker containing special characters
    content_special_speaker = """
User_123: Message from user with underscore
<!-- aclarai:id=blk_special ver=1 -->
^blk_special
"""
    blocks = chunker._parse_tier1_blocks(content_special_speaker)
    assert len(blocks) == 1
    assert blocks[0]["speaker"] == "User_123"

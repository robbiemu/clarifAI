"""
Comprehensive tests for embedding chunking module.
"""

from aclarai_shared.config import EmbeddingConfig, aclaraiConfig
from aclarai_shared.embedding.chunking import ChunkMetadata, UtteranceChunker


class TestChunkingModule:
    """Test the chunking module comprehensive functionality."""

    def test_chunking_module_attributes(self):
        """Test that chunking module has expected attributes."""
        from aclarai_shared.embedding import chunking

        assert hasattr(chunking, "UtteranceChunker")
        assert hasattr(chunking, "ChunkMetadata")
        assert hasattr(chunking, "TextNode")
        assert hasattr(chunking, "logger")

    def test_chunk_metadata_all_fields(self):
        """Test ChunkMetadata with all fields."""
        metadata = ChunkMetadata(
            aclarai_block_id="blk_comprehensive_001",
            chunk_index=5,
            original_text="This is the complete original text for comprehensive testing purposes.",
            text="This is the chunked portion of the text.",
        )
        assert metadata.aclarai_block_id == "blk_comprehensive_001"
        assert metadata.chunk_index == 5
        assert (
            metadata.original_text
            == "This is the complete original text for comprehensive testing purposes."
        )
        assert metadata.text == "This is the chunked portion of the text."

    def test_utterance_chunker_config_loading(self):
        """Test UtteranceChunker with various config settings."""
        config = aclaraiConfig()
        config.embedding = EmbeddingConfig(
            chunk_size=200,
            chunk_overlap=20,
            merge_colon_endings=False,
            merge_short_prefixes=False,
            min_chunk_tokens=3,
        )
        chunker = UtteranceChunker(config)
        assert chunker.config == config
        assert chunker.splitter is not None

    def test_utterance_chunker_default_config(self):
        """Test UtteranceChunker with default config loading."""
        chunker = UtteranceChunker()
        assert chunker.config is not None
        assert chunker.splitter is not None

    def test_parse_tier1_blocks_complex(self):
        """Test parsing complex tier1 blocks."""
        chunker = UtteranceChunker()
        tier1_content = """
<!-- aclarai:title=Complex Test Conversation -->
<!-- aclarai:created_at=2024-01-01T10:00:00Z -->
Alice: This is a complex message with multiple sentences.
It contains various punctuation marks! And questions?
And also some special characters: @, #, $, %.
<!-- aclarai:id=blk_complex_001 ver=1 -->
^blk_complex_001
Bob: I completely agree with your assessment. However, I think there's room
for improvement.
Let me explain my reasoning:
1. First point
2. Second point
3. Third point
<!-- aclarai:id=blk_complex_002 ver=2 -->
^blk_complex_002
Charlie: Here's some code: `print("hello world")` and a URL: https://example.com
<!-- aclarai:id=blk_complex_003 ver=1 -->
^blk_complex_003
"""
        blocks = chunker._parse_tier1_blocks(tier1_content)
        assert len(blocks) == 3
        assert blocks[0]["aclarai_id"] == "blk_complex_001"
        assert blocks[1]["aclarai_id"] == "blk_complex_002"
        assert blocks[2]["aclarai_id"] == "blk_complex_003"
        # Check content parsing - look for the actual special characters
        assert "@, #, $, %." in blocks[0]["text"]
        assert "First point" in blocks[1]["text"]
        assert "print(" in blocks[2]["text"]

    def test_chunk_utterance_block_various_sizes(self):
        """Test chunking blocks of various sizes."""
        chunker = UtteranceChunker()
        # Short text
        short_text = "Short message."
        chunks = chunker.chunk_utterance_block(short_text, "blk_short")
        assert len(chunks) >= 1
        assert all(chunk.aclarai_block_id == "blk_short" for chunk in chunks)
        # Medium text
        medium_text = " ".join([f"Sentence {i} with content." for i in range(10)])
        chunks = chunker.chunk_utterance_block(medium_text, "blk_medium")
        assert len(chunks) >= 1
        assert all(chunk.aclarai_block_id == "blk_medium" for chunk in chunks)
        # Very long text
        long_text = " ".join(
            [
                f"Very detailed sentence number {i} with lots of content to ensure we exceed chunk size limits."
                for i in range(100)
            ]
        )
        chunks = chunker.chunk_utterance_block(long_text, "blk_long")
        assert len(chunks) > 1
        assert all(chunk.aclarai_block_id == "blk_long" for chunk in chunks)

    def test_postprocessing_rules_comprehensive(self):
        """Test all postprocessing rules."""
        config = aclaraiConfig()
        config.embedding = EmbeddingConfig(
            merge_colon_endings=True,
            merge_short_prefixes=True,
            min_chunk_tokens=5,
        )
        chunker = UtteranceChunker(config)
        from aclarai_shared.embedding.chunking import TextNode

        # Test colon ending merge
        colon_chunks = [
            TextNode(text="This is a lead-in:", metadata={}),
            TextNode(text="followed by the actual content.", metadata={}),
        ]
        processed = chunker._apply_postprocessing_rules(colon_chunks)
        assert len(processed) == 1
        assert "lead-in: followed by" in processed[0].text
        # Test short prefix merge
        prefix_chunks = [
            TextNode(text="Note:", metadata={}),
            TextNode(
                text="This is the important information that follows.", metadata={}
            ),
        ]
        processed = chunker._apply_postprocessing_rules(prefix_chunks)
        assert len(processed) == 1
        assert "Note: This is the important" in processed[0].text

    def test_count_tokens_edge_cases(self):
        """Test token counting with edge cases."""
        chunker = UtteranceChunker()
        # Test various inputs
        assert chunker._count_tokens("") == 0
        assert chunker._count_tokens("   ") == 0  # Just spaces
        assert chunker._count_tokens("single") == 1
        assert chunker._count_tokens("word1 word2") == 2
        assert chunker._count_tokens("word1\nword2\tword3") == 3
        assert chunker._count_tokens("don't won't can't") == 3
        assert chunker._count_tokens("test@example.com") == 1
        assert chunker._count_tokens("123 456 789") == 3

    def test_tier1_blocks_integration_comprehensive(self):
        """Test complete tier1 processing with various edge cases."""
        chunker = UtteranceChunker()
        # Test with different speaker formats
        tier1_content = """
<!-- aclarai:title=Integration Test -->
User123: Message from user with numbers
<!-- aclarai:id=blk_user123 ver=1 -->
^blk_user123
Dr. Smith: Message from user with title and period
<!-- aclarai:id=blk_drsmith ver=1 -->
^blk_drsmith
user_with_underscores: Message from user with underscores
<!-- aclarai:id=blk_underscores ver=1 -->
^blk_underscores
"""
        chunks = chunker.chunk_tier1_blocks(tier1_content)
        # Should have chunks from all blocks
        assert len(chunks) >= 3
        block_ids = {chunk.aclarai_block_id for chunk in chunks}
        assert "blk_user123" in block_ids
        assert "blk_drsmith" in block_ids
        assert "blk_underscores" in block_ids

    def test_edge_cases_malformed_input(self):
        """Test handling of malformed input."""
        chunker = UtteranceChunker()
        # Missing speaker
        malformed1 = """
This is just text without a speaker
<!-- aclarai:id=blk_nospeaker ver=1 -->
^blk_nospeaker
"""
        blocks = chunker._parse_tier1_blocks(malformed1)
        # Should handle gracefully, may or may not create blocks
        assert isinstance(blocks, list)
        # Missing aclarai:id
        malformed2 = """
Speaker: This has no aclarai:id comment
^blk_noid
"""
        blocks = chunker._parse_tier1_blocks(malformed2)
        assert isinstance(blocks, list)
        # Duplicate block IDs
        malformed3 = """
Speaker1: First message
<!-- aclarai:id=blk_duplicate ver=1 -->
^blk_duplicate
Speaker2: Second message
<!-- aclarai:id=blk_duplicate ver=2 -->
^blk_duplicate
"""
        blocks = chunker._parse_tier1_blocks(malformed3)
        assert isinstance(blocks, list)

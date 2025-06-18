"""
Tests for embedding module initialization and basic imports.
"""

from aclarai_shared.embedding import chunking, models, storage


class TestEmbeddingInit:
    """Test that embedding module components can be loaded and have expected attributes."""

    def test_chunking_module_loads(self):
        """Test chunking module can be loaded."""
        # Check expected classes exist
        assert hasattr(chunking, "UtteranceChunker")
        assert hasattr(chunking, "ChunkMetadata")

    def test_models_module_loads(self):
        """Test models module can be loaded."""
        # Check expected classes exist
        assert hasattr(models, "EmbeddingGenerator")
        assert hasattr(models, "EmbeddedChunk")

    def test_storage_module_loads(self):
        """Test storage module can be loaded."""
        # Check expected classes exist
        assert hasattr(storage, "aclaraiVectorStore")
        assert hasattr(storage, "VectorStoreMetrics")

    def test_chunk_metadata_creation(self):
        """Test ChunkMetadata can be instantiated."""
        # Provide all required fields for ChunkMetadata
        metadata = chunking.ChunkMetadata(
            aclarai_block_id="block_test_001",  # Required
            chunk_index=0,
            original_text="This is the original full text for testing.",  # Required
            text="This is the chunked text part.",  # Required
        )

        # Assert the fields that were actually set and exist
        assert metadata.aclarai_block_id == "block_test_001"
        assert metadata.chunk_index == 0
        assert metadata.original_text == "This is the original full text for testing."
        assert metadata.text == "This is the chunked text part."

    def test_embedded_chunk_creation(self):
        """Test EmbeddedChunk can be instantiated."""
        # 1. First, create a valid ChunkMetadata instance.
        # The "content" from the original test likely corresponds to `ChunkMetadata.text`.
        # The `metadata={"test": "value"}` has no direct place in the current `ChunkMetadata`
        # definition. If this information is crucial, it would need to be stored within
        # `ChunkMetadata` (e.g., as part of `original_text` or if `ChunkMetadata` had a generic dict field).
        test_meta = chunking.ChunkMetadata(
            aclarai_block_id="block_embed_002",
            chunk_index=1,
            original_text="Original text before chunking for embedding test.",
            text="Test content",  # This corresponds to the old "content"
        )

        # 2. Now create the EmbeddedChunk instance using the test_meta
        chunk = models.EmbeddedChunk(
            chunk_metadata=test_meta,  # Pass the ChunkMetadata object
            embedding=[0.1, 0.2, 0.3],
            model_name="test_embedding_model",  # Required
            embedding_dim=3,  # Required (should match len(embedding))
        )

        # 3. Assert based on the actual structure
        # Access "content" via chunk_metadata.text
        assert chunk.chunk_metadata.text == "Test content"
        assert chunk.embedding == [0.1, 0.2, 0.3]
        # We assert the other required fields:
        assert chunk.model_name == "test_embedding_model"
        assert chunk.embedding_dim == 3
        assert chunk.chunk_metadata == test_meta  # You can assert the whole object too

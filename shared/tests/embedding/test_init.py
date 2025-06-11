"""
Tests for embedding module initialization and basic imports.
"""

from clarifai_shared.embedding import chunking, models, storage


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
        assert hasattr(storage, "ClarifAIVectorStore")
        assert hasattr(storage, "VectorStoreMetrics")

    def test_chunk_metadata_creation(self):
        """Test ChunkMetadata can be instantiated."""
        metadata = chunking.ChunkMetadata(
            chunk_index=0, source_file="test.txt", document_id="doc_123"
        )

        assert metadata.chunk_index == 0
        assert metadata.source_file == "test.txt"
        assert metadata.document_id == "doc_123"

    def test_embedded_chunk_creation(self):
        """Test EmbeddedChunk can be instantiated."""
        chunk = models.EmbeddedChunk(
            content="Test content",
            embedding=[0.1, 0.2, 0.3],
            metadata={"test": "value"},
        )

        assert chunk.content == "Test content"
        assert chunk.embedding == [0.1, 0.2, 0.3]
        assert chunk.metadata == {"test": "value"}

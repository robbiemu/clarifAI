"""
Tests for embedding module pipeline and initialization.
"""

from unittest.mock import Mock, patch

from clarifai_shared.embedding import (
    EmbeddingResult,
    UtteranceChunker,
    ChunkMetadata,
    EmbeddingGenerator,
    EmbeddedChunk,
    ClarifAIVectorStore,
    VectorStoreMetrics,
)
from clarifai_shared.config import ClarifAIConfig, EmbeddingConfig, DatabaseConfig


class TestEmbeddingResult:
    """Test cases for EmbeddingResult dataclass."""

    def test_embedding_result_creation(self):
        """Test EmbeddingResult creation."""
        metrics = VectorStoreMetrics(100, 95, 5)

        result = EmbeddingResult(
            success=True,
            total_chunks=100,
            embedded_chunks=95,
            stored_chunks=90,
            failed_chunks=5,
            metrics=metrics,
            errors=["Test error"],
        )

        assert result.success is True
        assert result.total_chunks == 100
        assert result.embedded_chunks == 95
        assert result.stored_chunks == 90
        assert result.failed_chunks == 5
        assert result.metrics == metrics
        assert result.errors == ["Test error"]

    def test_embedding_result_defaults(self):
        """Test EmbeddingResult with minimal data."""
        metrics = VectorStoreMetrics(0, 0, 0)

        result = EmbeddingResult(
            success=False,
            total_chunks=0,
            embedded_chunks=0,
            stored_chunks=0,
            failed_chunks=0,
            metrics=metrics,
            errors=[],
        )

        assert result.success is False
        assert result.total_chunks == 0
        assert len(result.errors) == 0


class TestEmbeddingPipeline:
    """Test cases for EmbeddingPipeline."""

    def test_embedding_pipeline_init_with_config(self, integration_mode):
        """Test EmbeddingPipeline initialization with config."""
        from clarifai_shared.embedding import EmbeddingPipeline

        config = ClarifAIConfig()
        config.embedding = EmbeddingConfig()
        config.database = DatabaseConfig(
            host="localhost",
            port=5432,
            user="test_user",
            password="test_pass",
            database="test_db",
        )

        if not integration_mode:
            with (
                patch(
                    "clarifai_shared.embedding.pipeline.ClarifAIVectorStore"
                ) as mock_vector_store,
                patch(
                    "clarifai_shared.embedding.pipeline.EmbeddingGenerator"
                ) as mock_generator,
                patch(
                    "clarifai_shared.embedding.pipeline.UtteranceChunker"
                ) as mock_chunker,
            ):
                # Setup mocks
                mock_chunker.return_value = Mock()
                mock_generator.return_value = Mock()
                mock_vector_store.return_value = Mock()

                pipeline = EmbeddingPipeline(config=config)
                assert pipeline.config == config
                assert hasattr(pipeline, "chunker")
                assert hasattr(pipeline, "embedding_generator")
                assert hasattr(pipeline, "vector_store")
        else:
            # Integration test - requires real PostgreSQL service
            pipeline = EmbeddingPipeline(config=config)
            assert pipeline.config == config
            assert hasattr(pipeline, "chunker")
            assert hasattr(pipeline, "embedding_generator")
            assert hasattr(pipeline, "vector_store")

    def test_embedding_pipeline_init_default_config(self, integration_mode):
        """Test EmbeddingPipeline initialization with default config."""
        from clarifai_shared.embedding import EmbeddingPipeline

        if not integration_mode:
            with (
                patch(
                    "clarifai_shared.embedding.pipeline.ClarifAIVectorStore"
                ) as mock_vector_store,
                patch(
                    "clarifai_shared.embedding.pipeline.EmbeddingGenerator"
                ) as mock_generator,
                patch(
                    "clarifai_shared.embedding.pipeline.UtteranceChunker"
                ) as mock_chunker,
            ):
                # Setup mocks
                mock_chunker.return_value = Mock()
                mock_generator.return_value = Mock()
                mock_vector_store.return_value = Mock()

                pipeline = EmbeddingPipeline()
                assert pipeline.config is not None
        else:
            # Integration test - requires real PostgreSQL service
            pipeline = EmbeddingPipeline()
            assert pipeline.config is not None

    def test_process_tier1_content_empty(self, integration_mode):
        """Test processing empty Tier 1 content."""
        from clarifai_shared.embedding import EmbeddingPipeline

        config = ClarifAIConfig()
        config.embedding = EmbeddingConfig()
        config.database = DatabaseConfig(
            host="localhost",
            port=5432,
            user="test_user",
            password="test_pass",
            database="test_db",
        )

        if not integration_mode:
            with (
                patch(
                    "clarifai_shared.embedding.pipeline.ClarifAIVectorStore"
                ) as mock_vector_store,
                patch(
                    "clarifai_shared.embedding.pipeline.EmbeddingGenerator"
                ) as mock_generator,
                patch(
                    "clarifai_shared.embedding.pipeline.UtteranceChunker"
                ) as mock_chunker,
            ):
                # Setup mocks
                mock_chunker.return_value = Mock()
                mock_generator.return_value = Mock()
                mock_vector_store.return_value = Mock()

                pipeline = EmbeddingPipeline(config=config)
                result = pipeline.process_tier1_content("")

                assert isinstance(result, EmbeddingResult)
                assert result.success is False
                assert result.total_chunks == 0
        else:
            # Integration test - requires real PostgreSQL service
            pipeline = EmbeddingPipeline(config=config)
            result = pipeline.process_tier1_content("")
            assert isinstance(result, EmbeddingResult)
            assert result.success is False
            assert result.total_chunks == 0


class TestEmbeddingModuleImports:
    """Test that all exports from embedding module can be imported."""

    def test_import_utterance_chunker(self):
        """Test importing UtteranceChunker."""
        assert UtteranceChunker is not None

    def test_import_chunk_metadata(self):
        """Test importing ChunkMetadata."""
        assert ChunkMetadata is not None

    def test_import_embedding_generator(self):
        """Test importing EmbeddingGenerator."""
        assert EmbeddingGenerator is not None

    def test_import_embedded_chunk(self):
        """Test importing EmbeddedChunk."""
        assert EmbeddedChunk is not None

    def test_import_vector_store(self):
        """Test importing ClarifAIVectorStore."""
        assert ClarifAIVectorStore is not None

    def test_import_vector_store_metrics(self):
        """Test importing VectorStoreMetrics."""
        assert VectorStoreMetrics is not None

    def test_import_embedding_result(self):
        """Test importing EmbeddingResult."""
        assert EmbeddingResult is not None

    def test_chunk_metadata_creation(self):
        """Test ChunkMetadata dataclass creation."""
        metadata = ChunkMetadata(
            chunk_id="chunk_123",
            block_id="blk_456",
            start_index=0,
            end_index=100,
            token_count=25,
            character_count=100,
        )

        assert metadata.chunk_id == "chunk_123"
        assert metadata.block_id == "blk_456"
        assert metadata.start_index == 0
        assert metadata.end_index == 100
        assert metadata.token_count == 25
        assert metadata.character_count == 100

    def test_embedded_chunk_creation(self):
        """Test EmbeddedChunk dataclass creation."""
        metadata = ChunkMetadata(
            chunk_id="chunk_123",
            block_id="blk_456",
            start_index=0,
            end_index=100,
            token_count=25,
            character_count=100,
        )

        chunk = EmbeddedChunk(
            text="Test chunk text", embedding=[0.1, 0.2, 0.3], metadata=metadata
        )

        assert chunk.text == "Test chunk text"
        assert chunk.embedding == [0.1, 0.2, 0.3]
        assert chunk.metadata == metadata

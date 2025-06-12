"""
Tests for embedding module __init__.py file.
"""

import os
from unittest.mock import Mock, patch

import clarifai_shared.embedding as embedding_module
from clarifai_shared.embedding import (
    EmbeddingResult,
    VectorStoreMetrics,
    EmbeddingPipeline,
)
from clarifai_shared.config import ClarifAIConfig


class TestEmbeddingInitFile:
    """Test that embedding __init__.py file loads correctly."""

    def test_init_file_loads(self):
        """Test that the embedding __init__.py file can be loaded directly."""
        # Check for expected attributes
        expected_all = [
            "UtteranceChunker",
            "ChunkMetadata",
            "EmbeddingGenerator",
            "EmbeddedChunk",
            "ClarifAIVectorStore",
            "VectorStoreMetrics",
            "EmbeddingPipeline",
        ]

        if hasattr(embedding_module, "__all__"):
            for item in expected_all:
                assert item in embedding_module.__all__

    def test_init_file_exists(self):
        """Test that the embedding __init__.py file exists."""
        init_path = os.path.join(
            os.path.dirname(__file__), "../../clarifai_shared/embedding/__init__.py"
        )
        assert os.path.exists(init_path)

    def test_embedding_result_dataclass(self):
        """Test EmbeddingResult dataclass creation."""
        metrics = VectorStoreMetrics(
            total_vectors=10, successful_inserts=8, failed_inserts=2
        )

        result = EmbeddingResult(
            success=True,
            total_chunks=10,
            embedded_chunks=8,
            stored_chunks=8,
            failed_chunks=2,
            metrics=metrics,
            errors=["test error"],
        )

        assert result.success is True
        assert result.total_chunks == 10
        assert result.embedded_chunks == 8
        assert result.stored_chunks == 8
        assert result.failed_chunks == 2
        assert result.metrics == metrics
        assert result.errors == ["test error"]

    def test_embedding_pipeline_init(self, integration_mode):
        """Test EmbeddingPipeline initialization with configurable dependencies."""
        config = ClarifAIConfig()

        if not integration_mode:
            with (
                patch(
                    "clarifai_shared.embedding.storage.ClarifAIVectorStore"
                ) as mock_vector_store,
                patch(
                    "clarifai_shared.embedding.models.EmbeddingGenerator"
                ) as mock_generator,
                patch(
                    "clarifai_shared.embedding.chunking.UtteranceChunker"
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

    def test_embedding_pipeline_init_no_config(self, integration_mode):
        """Test EmbeddingPipeline initialization without config."""

        if not integration_mode:
            with (
                patch(
                    "clarifai_shared.embedding.storage.ClarifAIVectorStore"
                ) as mock_vector_store,
                patch(
                    "clarifai_shared.embedding.models.EmbeddingGenerator"
                ) as mock_generator,
                patch(
                    "clarifai_shared.embedding.chunking.UtteranceChunker"
                ) as mock_chunker,
            ):
                # Setup mocks
                mock_chunker.return_value = Mock()
                mock_generator.return_value = Mock()
                mock_vector_store.return_value = Mock()

                pipeline = EmbeddingPipeline()

                assert pipeline.config is not None
                assert hasattr(pipeline, "chunker")
                assert hasattr(pipeline, "embedding_generator")
                assert hasattr(pipeline, "vector_store")
        else:
            # Integration test - requires real PostgreSQL service
            pipeline = EmbeddingPipeline()
            assert pipeline.config is not None
            assert hasattr(pipeline, "chunker")
            assert hasattr(pipeline, "embedding_generator")
            assert hasattr(pipeline, "vector_store")

    def test_process_tier1_content_empty(self, integration_mode):
        """Test processing empty tier1 content."""

        if not integration_mode:
            with (
                patch(
                    "clarifai_shared.embedding.storage.ClarifAIVectorStore"
                ) as mock_vector_store,
                patch(
                    "clarifai_shared.embedding.models.EmbeddingGenerator"
                ) as mock_generator,
                patch(
                    "clarifai_shared.embedding.chunking.UtteranceChunker"
                ) as mock_chunker,
            ):
                # Setup mocks
                mock_chunker.return_value = Mock()
                mock_generator.return_value = Mock()
                mock_vector_store.return_value = Mock()

                pipeline = EmbeddingPipeline()
                result = pipeline.process_tier1_content("")

                assert isinstance(result, EmbeddingResult)
                assert result.success is False
                assert result.total_chunks == 0
        else:
            # Integration test - requires real PostgreSQL service
            pipeline = EmbeddingPipeline()
            result = pipeline.process_tier1_content("")
            assert isinstance(result, EmbeddingResult)
            assert result.success is False
            assert result.total_chunks == 0

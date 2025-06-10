"""
Tests for ClarifAI embedding pipeline functionality.

These tests verify the complete embedding pipeline including chunking,
embedding generation, and vector storage.
"""

import pytest
from unittest.mock import Mock, patch
from clarifai_shared.embedding import (
    EmbeddingPipeline,
    EmbeddingResult,
    VectorStoreMetrics,
)
from clarifai_shared.embedding.chunking import ChunkMetadata
from clarifai_shared.embedding.models import EmbeddedChunk
from clarifai_shared.config import ClarifAIConfig, EmbeddingConfig


@pytest.fixture
def mock_config():
    """Create a mock configuration for testing."""
    config = ClarifAIConfig()
    config.embedding = EmbeddingConfig(
        chunk_size=300,
        chunk_overlap=30,
        default_model="sentence-transformers/all-MiniLM-L6-v2",
        embed_dim=384,
    )
    return config


@pytest.fixture
def mock_pipeline_components():
    """Create mock pipeline components."""
    mock_chunker = Mock()
    mock_embedding_generator = Mock()
    mock_vector_store = Mock()

    return mock_chunker, mock_embedding_generator, mock_vector_store


def test_embedding_pipeline_initialization(mock_config):
    """Test that pipeline initializes with all components."""
    with (
        patch("clarifai_shared.embedding.load_config", return_value=mock_config),
        patch("clarifai_shared.embedding.UtteranceChunker") as mock_chunker_class,
        patch("clarifai_shared.embedding.EmbeddingGenerator") as mock_generator_class,
        patch("clarifai_shared.embedding.ClarifAIVectorStore") as mock_store_class,
    ):
        pipeline = EmbeddingPipeline(mock_config)

        assert pipeline.config == mock_config
        mock_chunker_class.assert_called_once_with(mock_config)
        mock_generator_class.assert_called_once_with(mock_config)
        mock_store_class.assert_called_once_with(mock_config)


def test_process_tier1_content_success(mock_config):
    """Test successful processing of Tier 1 content."""
    # Setup mock data
    mock_chunks = [
        ChunkMetadata("blk_001", 0, "Original text 1", "Chunk text 1"),
        ChunkMetadata("blk_002", 0, "Original text 2", "Chunk text 2"),
    ]

    mock_embedded_chunks = [
        EmbeddedChunk(mock_chunks[0], [0.1] * 384, "test-model", 384),
        EmbeddedChunk(mock_chunks[1], [0.2] * 384, "test-model", 384),
    ]

    mock_metrics = VectorStoreMetrics(
        total_vectors=2, successful_inserts=2, failed_inserts=0
    )

    with (
        patch("clarifai_shared.embedding.load_config", return_value=mock_config),
        patch("clarifai_shared.embedding.UtteranceChunker") as mock_chunker_class,
        patch("clarifai_shared.embedding.EmbeddingGenerator") as mock_generator_class,
        patch("clarifai_shared.embedding.ClarifAIVectorStore") as mock_store_class,
    ):
        # Setup mock methods
        mock_chunker = mock_chunker_class.return_value
        mock_chunker.chunk_tier1_blocks.return_value = mock_chunks

        mock_generator = mock_generator_class.return_value
        mock_generator.embed_chunks.return_value = mock_embedded_chunks
        mock_generator.validate_embeddings.return_value = {"status": "success"}

        mock_store = mock_store_class.return_value
        mock_store.store_embeddings.return_value = mock_metrics

        # Test the pipeline
        pipeline = EmbeddingPipeline(mock_config)
        result = pipeline.process_tier1_content("test tier1 content")

        # Verify results
        assert result.success is True
        assert result.total_chunks == 2
        assert result.embedded_chunks == 2
        assert result.stored_chunks == 2
        assert result.failed_chunks == 0
        assert len(result.errors) == 0


def test_process_tier1_content_no_chunks(mock_config):
    """Test processing when no chunks are generated."""
    with (
        patch("clarifai_shared.embedding.load_config", return_value=mock_config),
        patch("clarifai_shared.embedding.UtteranceChunker") as mock_chunker_class,
        patch("clarifai_shared.embedding.EmbeddingGenerator"),
        patch("clarifai_shared.embedding.ClarifAIVectorStore"),
    ):
        # Setup chunker to return no chunks
        mock_chunker = mock_chunker_class.return_value
        mock_chunker.chunk_tier1_blocks.return_value = []

        pipeline = EmbeddingPipeline(mock_config)
        result = pipeline.process_tier1_content("empty content")

        # Verify failure result
        assert result.success is False
        assert result.total_chunks == 0
        assert "No chunks generated from input content" in result.errors


def test_process_tier1_content_embedding_failure(mock_config):
    """Test processing when embedding generation fails."""
    mock_chunks = [ChunkMetadata("blk_001", 0, "Original", "Chunk")]

    with (
        patch("clarifai_shared.embedding.load_config", return_value=mock_config),
        patch("clarifai_shared.embedding.UtteranceChunker") as mock_chunker_class,
        patch("clarifai_shared.embedding.EmbeddingGenerator") as mock_generator_class,
        patch("clarifai_shared.embedding.ClarifAIVectorStore"),
    ):
        # Setup chunker to return chunks but generator to fail
        mock_chunker = mock_chunker_class.return_value
        mock_chunker.chunk_tier1_blocks.return_value = mock_chunks

        mock_generator = mock_generator_class.return_value
        mock_generator.embed_chunks.return_value = []  # No embeddings generated

        pipeline = EmbeddingPipeline(mock_config)
        result = pipeline.process_tier1_content("test content")

        # Verify failure result
        assert result.success is False
        assert result.total_chunks == 1
        assert result.embedded_chunks == 0
        assert "Failed to generate embeddings for chunks" in result.errors


def test_process_single_block_success(mock_config):
    """Test successful processing of a single block."""
    mock_chunks = [ChunkMetadata("blk_test", 0, "Test text", "Test text")]
    mock_embedded_chunks = [
        EmbeddedChunk(mock_chunks[0], [0.1] * 384, "test-model", 384)
    ]
    mock_metrics = VectorStoreMetrics(1, 1, 0)

    with (
        patch("clarifai_shared.embedding.load_config", return_value=mock_config),
        patch("clarifai_shared.embedding.UtteranceChunker") as mock_chunker_class,
        patch("clarifai_shared.embedding.EmbeddingGenerator") as mock_generator_class,
        patch("clarifai_shared.embedding.ClarifAIVectorStore") as mock_store_class,
    ):
        # Setup mocks
        mock_chunker = mock_chunker_class.return_value
        mock_chunker.chunk_utterance_block.return_value = mock_chunks

        mock_generator = mock_generator_class.return_value
        mock_generator.embed_chunks.return_value = mock_embedded_chunks

        mock_store = mock_store_class.return_value
        mock_store.delete_chunks_by_block_id.return_value = 0
        mock_store.store_embeddings.return_value = mock_metrics

        pipeline = EmbeddingPipeline(mock_config)
        result = pipeline.process_single_block("Test text", "blk_test")

        # Verify results
        assert result.success is True
        assert result.total_chunks == 1
        assert result.stored_chunks == 1

        # Verify delete was called for replacement
        mock_store.delete_chunks_by_block_id.assert_called_once_with("blk_test")


def test_process_single_block_with_replacement(mock_config):
    """Test single block processing with existing chunk replacement."""
    mock_chunks = [ChunkMetadata("blk_replace", 0, "New text", "New text")]
    mock_embedded_chunks = [
        EmbeddedChunk(mock_chunks[0], [0.1] * 384, "test-model", 384)
    ]
    mock_metrics = VectorStoreMetrics(1, 1, 0)

    with (
        patch("clarifai_shared.embedding.load_config", return_value=mock_config),
        patch("clarifai_shared.embedding.UtteranceChunker") as mock_chunker_class,
        patch("clarifai_shared.embedding.EmbeddingGenerator") as mock_generator_class,
        patch("clarifai_shared.embedding.ClarifAIVectorStore") as mock_store_class,
    ):
        mock_chunker = mock_chunker_class.return_value
        mock_chunker.chunk_utterance_block.return_value = mock_chunks

        mock_generator = mock_generator_class.return_value
        mock_generator.embed_chunks.return_value = mock_embedded_chunks

        mock_store = mock_store_class.return_value
        mock_store.delete_chunks_by_block_id.return_value = (
            2  # 2 existing chunks deleted
        )
        mock_store.store_embeddings.return_value = mock_metrics

        pipeline = EmbeddingPipeline(mock_config)
        result = pipeline.process_single_block(
            "New text", "blk_replace", replace_existing=True
        )

        assert result.success is True
        mock_store.delete_chunks_by_block_id.assert_called_once_with("blk_replace")


def test_search_similar_chunks(mock_config):
    """Test similarity search functionality."""
    mock_search_results = [
        (
            {
                "clarifai_block_id": "blk_001",
                "chunk_index": 0,
                "text": "Similar text 1",
            },
            0.95,
        ),
        (
            {
                "clarifai_block_id": "blk_002",
                "chunk_index": 0,
                "text": "Similar text 2",
            },
            0.87,
        ),
    ]

    with (
        patch("clarifai_shared.embedding.load_config", return_value=mock_config),
        patch("clarifai_shared.embedding.UtteranceChunker"),
        patch("clarifai_shared.embedding.EmbeddingGenerator"),
        patch("clarifai_shared.embedding.ClarifAIVectorStore") as mock_store_class,
    ):
        mock_store = mock_store_class.return_value
        mock_store.similarity_search.return_value = mock_search_results

        pipeline = EmbeddingPipeline(mock_config)
        results = pipeline.search_similar_chunks("test query", top_k=5)

        assert len(results) == 2
        assert results[0]["similarity_score"] == 0.95
        assert results[0]["clarifai_block_id"] == "blk_001"
        assert results[1]["similarity_score"] == 0.87

        mock_store.similarity_search.assert_called_once_with(
            query_text="test query", top_k=5, similarity_threshold=None
        )


def test_get_pipeline_status(mock_config):
    """Test pipeline status reporting."""
    mock_metrics = VectorStoreMetrics(100, 100, 0)

    with (
        patch("clarifai_shared.embedding.load_config", return_value=mock_config),
        patch("clarifai_shared.embedding.UtteranceChunker"),
        patch("clarifai_shared.embedding.EmbeddingGenerator") as mock_generator_class,
        patch("clarifai_shared.embedding.ClarifAIVectorStore") as mock_store_class,
    ):
        mock_store = mock_store_class.return_value
        mock_store.get_store_metrics.return_value = mock_metrics

        mock_generator = mock_generator_class.return_value
        mock_generator.embed_text.return_value = [0.1] * 384
        mock_generator.model_name = "test-model"

        pipeline = EmbeddingPipeline(mock_config)
        status = pipeline.get_pipeline_status()

        assert status["overall_status"] == "healthy"
        assert status["components"]["vector_store"]["status"] == "healthy"
        assert status["components"]["vector_store"]["total_vectors"] == 100
        assert status["components"]["embedding_model"]["status"] == "healthy"
        assert status["components"]["embedding_model"]["model_name"] == "test-model"
        assert status["components"]["chunker"]["status"] == "healthy"


def test_pipeline_exception_handling(mock_config):
    """Test that pipeline handles exceptions gracefully."""
    with (
        patch("clarifai_shared.embedding.load_config", return_value=mock_config),
        patch("clarifai_shared.embedding.UtteranceChunker") as mock_chunker_class,
        patch("clarifai_shared.embedding.EmbeddingGenerator"),
        patch("clarifai_shared.embedding.ClarifAIVectorStore"),
    ):
        # Setup chunker to raise an exception
        mock_chunker = mock_chunker_class.return_value
        mock_chunker.chunk_tier1_blocks.side_effect = Exception("Test exception")

        pipeline = EmbeddingPipeline(mock_config)
        result = pipeline.process_tier1_content("test content")

        # Verify graceful failure
        assert result.success is False
        assert len(result.errors) > 0
        assert "Embedding pipeline failed" in result.errors[0]


def test_embedding_result_dataclass():
    """Test EmbeddingResult dataclass functionality."""
    metrics = VectorStoreMetrics(10, 8, 2)
    result = EmbeddingResult(
        success=True,
        total_chunks=10,
        embedded_chunks=10,
        stored_chunks=8,
        failed_chunks=2,
        metrics=metrics,
        errors=["Warning: some chunks failed"],
    )

    assert result.success is True
    assert result.total_chunks == 10
    assert result.embedded_chunks == 10
    assert result.stored_chunks == 8
    assert result.failed_chunks == 2
    assert result.metrics == metrics
    assert len(result.errors) == 1

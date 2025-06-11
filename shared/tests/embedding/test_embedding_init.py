"""
Tests for embedding module __init__.py file.
"""

import os

import clarifai_shared.embedding as embedding_module
from clarifai_shared.embedding import (
    EmbeddingPipeline, 
    EmbeddingResult,
    UtteranceChunker,
    ChunkMetadata,
    EmbeddingGenerator,
    EmbeddedChunk,
    ClarifAIVectorStore,
    VectorStoreMetrics
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
        metrics = VectorStoreMetrics(total_vectors=10, successful_inserts=8, failed_inserts=2)
        
        result = EmbeddingResult(
            success=True,
            total_chunks=10,
            embedded_chunks=8,
            stored_chunks=8,
            failed_chunks=2,
            metrics=metrics,
            errors=["test error"]
        )
        
        assert result.success is True
        assert result.total_chunks == 10
        assert result.embedded_chunks == 8
        assert result.stored_chunks == 8
        assert result.failed_chunks == 2
        assert result.metrics == metrics
        assert result.errors == ["test error"]

    def test_embedding_pipeline_init(self):
        """Test EmbeddingPipeline initialization."""
        config = ClarifAIConfig()
        pipeline = EmbeddingPipeline(config=config)
        
        assert pipeline.config == config
        assert hasattr(pipeline, 'chunker')
        assert hasattr(pipeline, 'embedding_generator')
        assert hasattr(pipeline, 'vector_store')

    def test_embedding_pipeline_init_no_config(self):
        """Test EmbeddingPipeline initialization without config."""
        pipeline = EmbeddingPipeline()
        
        assert pipeline.config is not None
        assert hasattr(pipeline, 'chunker')
        assert hasattr(pipeline, 'embedding_generator')
        assert hasattr(pipeline, 'vector_store')

    def test_process_tier1_content_empty(self):
        """Test processing empty tier1 content."""
        pipeline = EmbeddingPipeline()
        result = pipeline.process_tier1_content("")
        
        assert isinstance(result, EmbeddingResult)
        assert result.success is False
        assert result.total_chunks == 0

    def test_process_single_block(self):
        """Test processing a single block."""
        pipeline = EmbeddingPipeline()
        result = pipeline.process_single_block(
            text="Test text for single block processing", 
            clarifai_block_id="blk_test_single",
            replace_existing=True
        )
        
        assert isinstance(result, EmbeddingResult)

    def test_search_similar_chunks(self):
        """Test similarity search in pipeline."""
        pipeline = EmbeddingPipeline()
        results = pipeline.search_similar_chunks(
            query_text="test query",
            top_k=5,
            similarity_threshold=0.8
        )
        
        assert isinstance(results, list)

    def test_get_pipeline_status(self):
        """Test getting pipeline status."""
        pipeline = EmbeddingPipeline()
        status = pipeline.get_pipeline_status()
        
        assert isinstance(status, dict)
        assert "components" in status
        assert "overall_status" in status

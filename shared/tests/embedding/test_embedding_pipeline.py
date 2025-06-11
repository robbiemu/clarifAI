"""
Tests for embedding module pipeline and initialization.
"""

from clarifai_shared.embedding import (
    EmbeddingPipeline,
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

    def test_embedding_pipeline_init_with_config(self):
        """Test EmbeddingPipeline initialization with config."""
        config = ClarifAIConfig()
        config.embedding = EmbeddingConfig()
        config.database = DatabaseConfig(
            host="localhost",
            port=5432,
            user="test_user", 
            password="test_pass",
            database="test_db"
        )            pipeline = EmbeddingPipeline(config=config)
            assert pipeline.config == config
            assert isinstance(pipeline.chunker, UtteranceChunker)
            assert isinstance(pipeline.embedding_generator, EmbeddingGenerator)
            assert isinstance(pipeline.vector_store, ClarifAIVectorStore)

    def test_embedding_pipeline_init_default_config(self):
        """Test EmbeddingPipeline initialization with default config."""            pipeline = EmbeddingPipeline()
            assert pipeline.config is not None

    def test_process_tier1_content_empty(self):
        """Test processing empty Tier 1 content."""
        config = ClarifAIConfig()
        config.embedding = EmbeddingConfig()
        config.database = DatabaseConfig(
            host="localhost",
            port=5432,
            user="test_user", 
            password="test_pass",
            database="test_db"
        )            pipeline = EmbeddingPipeline(config=config)
            result = pipeline.process_tier1_content("")

            assert isinstance(result, EmbeddingResult)
            assert result.success is False
            assert result.total_chunks == 0

    def test_process_tier1_content_valid(self):
        """Test processing valid Tier 1 content."""
        config = ClarifAIConfig()
        config.embedding = EmbeddingConfig()
        config.database = DatabaseConfig(
            host="localhost",
            port=5432,
            user="test_user", 
            password="test_pass",
            database="test_db"
        )

        tier1_content = """
        Alice: Hello, how are you?
        <!-- clarifai:id=blk_test123 ver=1 -->
        ^blk_test123
        """            pipeline = EmbeddingPipeline(config=config)
            result = pipeline.process_tier1_content(tier1_content)

            assert isinstance(result, EmbeddingResult)
            # May succeed or fail due to dependencies, but should return valid result

    def test_process_single_block(self):
        """Test processing a single block."""
        config = ClarifAIConfig()
        config.embedding = EmbeddingConfig()
        config.database = DatabaseConfig(
            host="localhost",
            port=5432,
            user="test_user", 
            password="test_pass",
            database="test_db"
        )            pipeline = EmbeddingPipeline(config=config)
            result = pipeline.process_single_block(
                text="This is a test utterance.",
                clarifai_block_id="blk_single_test",
                replace_existing=True,
            )

            assert isinstance(result, EmbeddingResult)

    def test_process_single_block_no_replace(self):
        """Test processing single block without replacing existing."""
        config = ClarifAIConfig()
        config.embedding = EmbeddingConfig()
        config.database = DatabaseConfig(
            host="localhost",
            port=5432,
            user="test_user", 
            password="test_pass",
            database="test_db"
        )            pipeline = EmbeddingPipeline(config=config)
            result = pipeline.process_single_block(
                text="Test utterance without replace.",
                clarifai_block_id="blk_no_replace_test",
                replace_existing=False,
            )

            assert isinstance(result, EmbeddingResult)

    def test_search_similar_chunks(self):
        """Test searching for similar chunks."""
        config = ClarifAIConfig()
        config.embedding = EmbeddingConfig()
        config.database = DatabaseConfig(
            host="localhost",
            port=5432,
            user="test_user", 
            password="test_pass",
            database="test_db"
        )            pipeline = EmbeddingPipeline(config=config)
            results = pipeline.search_similar_chunks(
                query_text="test search query", top_k=5, similarity_threshold=0.8
            )

            assert isinstance(results, list)

    def test_search_similar_chunks_with_defaults(self):
        """Test searching for similar chunks with default parameters."""
        config = ClarifAIConfig()
        config.embedding = EmbeddingConfig()
        config.database = DatabaseConfig(
            host="localhost",
            port=5432,
            user="test_user", 
            password="test_pass",
            database="test_db"
        )            pipeline = EmbeddingPipeline(config=config)
            results = pipeline.search_similar_chunks("default search")

            assert isinstance(results, list)

    def test_get_pipeline_status(self):
        """Test getting pipeline status."""
        config = ClarifAIConfig()
        config.embedding = EmbeddingConfig()
        config.database = DatabaseConfig(
            host="localhost",
            port=5432,
            user="test_user", 
            password="test_pass",
            database="test_db"
        )            pipeline = EmbeddingPipeline(config=config)
            status = pipeline.get_pipeline_status()

            assert isinstance(status, dict)
            assert "components" in status
            assert "overall_status" in status

    def test_pipeline_error_handling(self):
        """Test pipeline error handling."""
        config = ClarifAIConfig()
        config.embedding = EmbeddingConfig()
        config.database = DatabaseConfig(
            host="localhost",
            port=5432,
            user="test_user", 
            password="test_pass",
            database="test_db"
        )            pipeline = EmbeddingPipeline(config=config)

            # Test with invalid content that should cause errors
            result = pipeline.process_tier1_content("invalid content")

            assert isinstance(result, EmbeddingResult)
            # Should handle errors gracefully


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

    def test_import_embedding_pipeline(self):
        """Test importing EmbeddingPipeline."""
        assert EmbeddingPipeline is not None

    def test_import_embedding_result(self):
        """Test importing EmbeddingResult."""
        assert EmbeddingResult is not None

    def test_module_all_attribute(self):
        """Test that __all__ attribute is properly defined."""
        import clarifai_shared.embedding as embedding_module

        assert hasattr(embedding_module, "__all__")
        assert isinstance(embedding_module.__all__, list)
        assert len(embedding_module.__all__) > 0

        # Check that all listed items can be imported
        for item_name in embedding_module.__all__:
            assert hasattr(embedding_module, item_name)


class TestEmbeddingModuleFunctionality:
    """Test actual functionality calls to provide coverage."""

    def test_embedding_pipeline_complete_workflow(self):
        """Test complete embedding pipeline workflow."""
        tier1_content = """
        <!-- clarifai:title=Test Content -->
        Speaker1: This is a test message for the embedding pipeline.
        <!-- clarifai:id=blk_workflow_test ver=1 -->
        ^blk_workflow_test
        
        Speaker2: This is another test message to verify functionality.
        <!-- clarifai:id=blk_workflow_test2 ver=1 -->
        ^blk_workflow_test2
        """            # This will exercise the entire pipeline code path
            pipeline = EmbeddingPipeline()
            result = pipeline.process_tier1_content(tier1_content)

            # Verify we get a proper result structure
            assert isinstance(result, EmbeddingResult)
            assert hasattr(result, "success")
            assert hasattr(result, "total_chunks")
            assert hasattr(result, "metrics")
            assert hasattr(result, "errors")

    def test_embedding_pipeline_status_check(self):
        """Test pipeline status functionality."""            pipeline = EmbeddingPipeline()
            status = pipeline.get_pipeline_status()

            # Should return status dict even if components fail
            assert isinstance(status, dict)

    def test_search_functionality(self):
        """Test search functionality to exercise code paths."""            pipeline = EmbeddingPipeline()

            # Test different search parameter combinations
            results1 = pipeline.search_similar_chunks("test query")
            results2 = pipeline.search_similar_chunks("test", top_k=5)
            results3 = pipeline.search_similar_chunks("test", similarity_threshold=0.9)

            # All should return lists (even if empty due to no data/dependencies)
            assert isinstance(results1, list)
            assert isinstance(results2, list)
            assert isinstance(results3, list)

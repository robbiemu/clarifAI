"""
Tests for embedding storage components.
"""

from unittest.mock import Mock, patch

from clarifai_shared.embedding.storage import ClarifAIVectorStore, VectorStoreMetrics
from clarifai_shared.embedding.models import EmbeddedChunk, ChunkMetadata
from clarifai_shared.config import ClarifAIConfig, DatabaseConfig


class TestVectorStoreMetrics:
    """Test cases for VectorStoreMetrics dataclass."""

    def test_vector_store_metrics_creation(self):
        """Test VectorStoreMetrics creation."""
        metrics = VectorStoreMetrics(
            total_vectors=100, successful_inserts=95, failed_inserts=5
        )

        assert metrics.total_vectors == 100
        assert metrics.successful_inserts == 95
        assert metrics.failed_inserts == 5

    def test_vector_store_metrics_default(self):
        """Test VectorStoreMetrics with defaults."""
        metrics = VectorStoreMetrics(50, 45, 5)

        assert metrics.total_vectors == 50
        assert metrics.successful_inserts == 45
        assert metrics.failed_inserts == 5

    def test_vector_store_metrics_equality(self):
        """Test VectorStoreMetrics equality."""
        metrics1 = VectorStoreMetrics(10, 8, 2)
        metrics2 = VectorStoreMetrics(10, 8, 2)
        metrics3 = VectorStoreMetrics(10, 9, 1)

        assert metrics1 == metrics2
        assert metrics1 != metrics3


class TestClarifAIVectorStore:
    """Test cases for ClarifAIVectorStore with configurable dependencies."""

    def test_vector_store_init_with_config(self, integration_mode):
        """Test ClarifAIVectorStore initialization with config."""
        config = ClarifAIConfig()
        config.database = DatabaseConfig(
            host="localhost",
            port=5432,
            database="clarifai_test",
            user="test_user",
            password="test_pass",
        )

        if not integration_mode:
            with patch(
                "clarifai_shared.embedding.storage.create_engine"
            ) as mock_create_engine:
                mock_engine = Mock()
                mock_create_engine.return_value = mock_engine
                vector_store = ClarifAIVectorStore(config=config)
                assert vector_store.config == config
        else:
            # Integration test - requires real PostgreSQL service
            vector_store = ClarifAIVectorStore(config=config)
            assert vector_store.config == config

    def test_vector_store_init_default_config(self, integration_mode):
        """Test ClarifAIVectorStore initialization with default config."""
        if not integration_mode:
            with patch(
                "clarifai_shared.embedding.storage.create_engine"
            ) as mock_create_engine:
                mock_engine = Mock()
                mock_create_engine.return_value = mock_engine
                vector_store = ClarifAIVectorStore()
                assert vector_store.config is not None
        else:
            # Integration test - requires real PostgreSQL service
            vector_store = ClarifAIVectorStore()
            assert vector_store.config is not None

    def test_store_embeddings(self, integration_mode):
        """Test storing embeddings in vector store."""
        config = ClarifAIConfig()
        config.database = DatabaseConfig(
            host="localhost",
            port=5432,
            user="test_user",
            password="test_pass",
            database="test_db",
        )

        # Create test embedded chunks
        chunk_metadata = ChunkMetadata(
            clarifai_block_id="blk_store_test",
            chunk_index=0,
            original_text="Test original text",
            text="Test chunk text",
        )

        embedded_chunks = [
            EmbeddedChunk(
                chunk_metadata=chunk_metadata,
                embedding=[0.1, 0.2, 0.3],
                model_name="test-model",
                embedding_dim=3,
            )
        ]

        if not integration_mode:
            with patch("clarifai_shared.embedding.storage.create_engine"):
                vector_store = ClarifAIVectorStore(config=config)
                metrics = vector_store.store_embeddings(embedded_chunks)
                assert isinstance(metrics, VectorStoreMetrics)
        else:
            # Integration test - requires real PostgreSQL service
            vector_store = ClarifAIVectorStore(config=config)
            metrics = vector_store.store_embeddings(embedded_chunks)
            assert isinstance(metrics, VectorStoreMetrics)

    def test_store_embeddings_empty_list(self, integration_mode):
        """Test storing empty list of embeddings."""
        config = ClarifAIConfig()
        config.database = DatabaseConfig(
            host="localhost",
            port=5432,
            user="test_user",
            password="test_pass",
            database="test_db",
        )

        if not integration_mode:
            with patch("clarifai_shared.embedding.storage.create_engine"):
                vector_store = ClarifAIVectorStore(config=config)
                metrics = vector_store.store_embeddings([])
                assert metrics.total_vectors == 0
                assert metrics.successful_inserts == 0
                assert metrics.failed_inserts == 0
        else:
            # Integration test - requires real PostgreSQL service
            vector_store = ClarifAIVectorStore(config=config)
            metrics = vector_store.store_embeddings([])
            assert metrics.total_vectors == 0
            assert metrics.successful_inserts == 0
            assert metrics.failed_inserts == 0

    def test_similarity_search(self, integration_mode):
        """Test similarity search functionality."""
        config = ClarifAIConfig()
        config.database = DatabaseConfig(
            host="localhost",
            port=5432,
            user="test_user",
            password="test_pass",
            database="test_db",
        )

        if not integration_mode:
            with patch("clarifai_shared.embedding.storage.create_engine"):
                vector_store = ClarifAIVectorStore(config=config)
                results = vector_store.similarity_search(
                    query_text="test query", top_k=5, similarity_threshold=0.8
                )
                assert isinstance(results, list)
        else:
            # Integration test - requires real PostgreSQL service
            vector_store = ClarifAIVectorStore(config=config)
            results = vector_store.similarity_search(
                query_text="test query", top_k=5, similarity_threshold=0.8
            )
            assert isinstance(results, list)

    def test_delete_chunks_by_block_id(self, integration_mode):
        """Test deleting chunks by block ID."""
        config = ClarifAIConfig()
        config.database = DatabaseConfig(
            host="localhost",
            port=5432,
            user="test_user",
            password="test_pass",
            database="test_db",
        )

        if not integration_mode:
            with patch("clarifai_shared.embedding.storage.create_engine"):
                vector_store = ClarifAIVectorStore(config=config)
                deleted_count = vector_store.delete_chunks_by_block_id(
                    "blk_delete_test"
                )
                assert isinstance(deleted_count, int)
                assert deleted_count >= 0
        else:
            # Integration test - requires real PostgreSQL service
            vector_store = ClarifAIVectorStore(config=config)
            deleted_count = vector_store.delete_chunks_by_block_id("blk_delete_test")
            assert isinstance(deleted_count, int)
            assert deleted_count >= 0

    def test_get_store_metrics(self, integration_mode):
        """Test getting store metrics."""
        config = ClarifAIConfig()
        config.database = DatabaseConfig(
            host="localhost",
            port=5432,
            user="test_user",
            password="test_pass",
            database="test_db",
        )

        if not integration_mode:
            with patch("clarifai_shared.embedding.storage.create_engine"):
                vector_store = ClarifAIVectorStore(config=config)
                metrics = vector_store.get_store_metrics()
                assert isinstance(metrics, VectorStoreMetrics)
        else:
            # Integration test - requires real PostgreSQL service
            vector_store = ClarifAIVectorStore(config=config)
            metrics = vector_store.get_store_metrics()
            assert isinstance(metrics, VectorStoreMetrics)

    def test_ensure_table_exists(self, integration_mode):
        """Test table creation/verification."""
        config = ClarifAIConfig()
        config.database = DatabaseConfig(
            host="localhost",
            port=5432,
            user="test_user",
            password="test_pass",
            database="test_db",
        )

        if not integration_mode:
            with patch("clarifai_shared.embedding.storage.create_engine"):
                vector_store = ClarifAIVectorStore(config=config)
                # This should not raise an exception even if DB isn't available
                vector_store._ensure_table_exists()
        else:
            # Integration test - requires real PostgreSQL service
            vector_store = ClarifAIVectorStore(config=config)
            vector_store._ensure_table_exists()

    def test_get_connection(self, integration_mode):
        """Test database connection."""
        config = ClarifAIConfig()
        config.database = DatabaseConfig(
            host="localhost",
            port=5432,
            user="test_user",
            password="test_pass",
            database="test_db",
        )

        if not integration_mode:
            with patch("clarifai_shared.embedding.storage.create_engine"):
                vector_store = ClarifAIVectorStore(config=config)
                with vector_store._get_connection() as conn:
                    assert conn is not None
        else:
            # Integration test - requires real PostgreSQL service
            vector_store = ClarifAIVectorStore(config=config)
            with vector_store._get_connection() as conn:
                assert conn is not None

    def test_initialize_vector_store(self, integration_mode):
        """Test vector store initialization."""
        config = ClarifAIConfig()
        config.database = DatabaseConfig(
            host="localhost",
            port=5432,
            user="test_user",
            password="test_pass",
            database="test_db",
        )

        if not integration_mode:
            with patch("clarifai_shared.embedding.storage.create_engine"):
                vector_store = ClarifAIVectorStore(config=config)
                vector_store._initialize_vector_store()
        else:
            # Integration test - requires real PostgreSQL service
            vector_store = ClarifAIVectorStore(config=config)
            vector_store._initialize_vector_store()

    def test_create_embedding_vector(self, integration_mode):
        """Test embedding vector creation from text."""
        config = ClarifAIConfig()
        config.database = DatabaseConfig(
            host="localhost",
            port=5432,
            user="test_user",
            password="test_pass",
            database="test_db",
        )

        if not integration_mode:
            with patch("clarifai_shared.embedding.storage.create_engine"):
                vector_store = ClarifAIVectorStore(config=config)
                embedding = vector_store._create_embedding_vector("test text")
                assert isinstance(embedding, list)
                assert all(isinstance(x, (int, float)) for x in embedding)
        else:
            # Integration test - requires real PostgreSQL service
            vector_store = ClarifAIVectorStore(config=config)
            embedding = vector_store._create_embedding_vector("test text")
            assert isinstance(embedding, list)
            assert all(isinstance(x, (int, float)) for x in embedding)

    def test_format_vector_for_db(self, integration_mode):
        """Test vector formatting for database storage."""
        config = ClarifAIConfig()
        config.database = DatabaseConfig(
            host="localhost",
            port=5432,
            user="test_user",
            password="test_pass",
            database="test_db",
        )

        if not integration_mode:
            with patch("clarifai_shared.embedding.storage.create_engine"):
                vector_store = ClarifAIVectorStore(config=config)
                test_vector = [0.1, 0.2, 0.3, 0.4]
                formatted = vector_store._format_vector_for_db(test_vector)
                # Should be formatted as string representation
                assert isinstance(formatted, str)
        else:
            # Integration test - requires real PostgreSQL service
            vector_store = ClarifAIVectorStore(config=config)
            test_vector = [0.1, 0.2, 0.3, 0.4]
            formatted = vector_store._format_vector_for_db(test_vector)
            assert isinstance(formatted, str)

    def test_validate_embedding_dimensions(self, integration_mode):
        """Test embedding dimension validation."""
        config = ClarifAIConfig()
        config.database = DatabaseConfig(
            host="localhost",
            port=5432,
            user="test_user",
            password="test_pass",
            database="test_db",
        )

        # Test valid embeddings
        valid_embeddings = [
            EmbeddedChunk(
                chunk_metadata=ChunkMetadata(
                    clarifai_block_id="blk_test",
                    chunk_index=0,
                    original_text="Test",
                    text="Test",
                ),
                embedding=[0.1, 0.2, 0.3],
                model_name="test",
                embedding_dim=3,
            )
        ]

        if not integration_mode:
            with patch("clarifai_shared.embedding.storage.create_engine"):
                vector_store = ClarifAIVectorStore(config=config)
                is_valid = vector_store._validate_embedding_dimensions(valid_embeddings)
                assert isinstance(is_valid, bool)
        else:
            # Integration test - requires real PostgreSQL service
            vector_store = ClarifAIVectorStore(config=config)
            is_valid = vector_store._validate_embedding_dimensions(valid_embeddings)
            assert isinstance(is_valid, bool)

    def test_batch_insert_embeddings(self, integration_mode):
        """Test batch insertion of embeddings."""
        config = ClarifAIConfig()
        config.database = DatabaseConfig(
            host="localhost",
            port=5432,
            user="test_user",
            password="test_pass",
            database="test_db",
        )

        embedded_chunks = [
            EmbeddedChunk(
                chunk_metadata=ChunkMetadata(
                    clarifai_block_id="blk_batch_test",
                    chunk_index=0,
                    original_text="Test original",
                    text="Test chunk",
                ),
                embedding=[0.1, 0.2, 0.3],
                model_name="test-model",
                embedding_dim=3,
            )
        ]

        if not integration_mode:
            with patch("clarifai_shared.embedding.storage.create_engine"):
                vector_store = ClarifAIVectorStore(config=config)
                result = vector_store._batch_insert_embeddings(embedded_chunks)
                assert isinstance(result, dict)
                assert "successful" in result
                assert "failed" in result
        else:
            # Integration test - requires real PostgreSQL service
            vector_store = ClarifAIVectorStore(config=config)
            result = vector_store._batch_insert_embeddings(embedded_chunks)
            assert isinstance(result, dict)
            assert "successful" in result
            assert "failed" in result

    def test_execute_similarity_query(self, integration_mode):
        """Test similarity query execution."""
        config = ClarifAIConfig()
        config.database = DatabaseConfig(
            host="localhost",
            port=5432,
            user="test_user",
            password="test_pass",
            database="test_db",
        )

        query_vector = [0.1, 0.2, 0.3]

        if not integration_mode:
            with patch("clarifai_shared.embedding.storage.create_engine"):
                vector_store = ClarifAIVectorStore(config=config)
                results = vector_store._execute_similarity_query(
                    query_vector=query_vector, top_k=10, similarity_threshold=0.8
                )
                assert isinstance(results, list)
        else:
            # Integration test - requires real PostgreSQL service
            vector_store = ClarifAIVectorStore(config=config)
            results = vector_store._execute_similarity_query(
                query_vector=query_vector, top_k=10, similarity_threshold=0.8
            )
            assert isinstance(results, list)

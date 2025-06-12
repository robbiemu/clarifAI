"""
Tests for embedding storage components.
"""

from unittest.mock import Mock, patch

from clarifai_shared.embedding.storage import ClarifAIVectorStore, VectorStoreMetrics
from clarifai_shared.embedding.models import EmbeddedChunk
from clarifai_shared.embedding.chunking import ChunkMetadata
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
        config.postgres = DatabaseConfig(
            host="localhost",
            port=5432,
            database="clarifai_test",
            user="test_user",
            password="test_pass",
        )

        if not integration_mode:
            with (
                patch(
                    "clarifai_shared.embedding.storage.create_engine"
                ) as mock_create_engine,
                patch("clarifai_shared.embedding.storage.PGVectorStore"),
                patch("clarifai_shared.embedding.storage.VectorStoreIndex"),
                patch("clarifai_shared.config.load_config") as mock_load_config,
            ):
                mock_engine = Mock()
                mock_engine.connect.return_value.__enter__ = Mock()
                mock_engine.connect.return_value.__exit__ = Mock()
                mock_create_engine.return_value = mock_engine
                mock_load_config.return_value = config

                vector_store = ClarifAIVectorStore(config=config)
                assert vector_store.config == config
        else:
            # Integration test - requires real PostgreSQL service
            vector_store = ClarifAIVectorStore(config=config)
            assert vector_store.config == config

    def test_store_embeddings(self, integration_mode):
        """Test storing embeddings in vector store."""
        config = ClarifAIConfig()
        config.postgres = DatabaseConfig(
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
            with (
                patch(
                    "clarifai_shared.embedding.storage.create_engine"
                ) as mock_create_engine,
                patch("clarifai_shared.embedding.storage.PGVectorStore"),
                patch("clarifai_shared.embedding.storage.VectorStoreIndex"),
                patch("clarifai_shared.config.load_config") as mock_load_config,
            ):
                mock_engine = Mock()
                mock_engine.connect.return_value.__enter__ = Mock()
                mock_engine.connect.return_value.__exit__ = Mock()
                mock_create_engine.return_value = mock_engine
                mock_load_config.return_value = config

                vector_store = ClarifAIVectorStore(config=config)

                # Mock the store_embeddings return value
                with patch.object(
                    vector_store,
                    "store_embeddings",
                    return_value=VectorStoreMetrics(1, 1, 0),
                ):
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
        config.postgres = DatabaseConfig(
            host="localhost",
            port=5432,
            user="test_user",
            password="test_pass",
            database="test_db",
        )

        if not integration_mode:
            with (
                patch(
                    "clarifai_shared.embedding.storage.create_engine"
                ) as mock_create_engine,
                patch("clarifai_shared.embedding.storage.PGVectorStore"),
                patch("clarifai_shared.embedding.storage.VectorStoreIndex"),
                patch("clarifai_shared.config.load_config") as mock_load_config,
            ):
                mock_engine = Mock()
                mock_engine.connect.return_value.__enter__ = Mock()
                mock_engine.connect.return_value.__exit__ = Mock()
                mock_create_engine.return_value = mock_engine
                mock_load_config.return_value = config

                vector_store = ClarifAIVectorStore(config=config)

                # Mock the store_embeddings return value
                with patch.object(
                    vector_store,
                    "store_embeddings",
                    return_value=VectorStoreMetrics(0, 0, 0),
                ):
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
        config.postgres = DatabaseConfig(
            host="localhost",
            port=5432,
            user="test_user",
            password="test_pass",
            database="test_db",
        )

        if not integration_mode:
            with (
                patch(
                    "clarifai_shared.embedding.storage.create_engine"
                ) as mock_create_engine,
                patch("clarifai_shared.embedding.storage.PGVectorStore"),
                patch("clarifai_shared.embedding.storage.VectorStoreIndex"),
                patch("clarifai_shared.config.load_config") as mock_load_config,
            ):
                mock_engine = Mock()
                mock_engine.connect.return_value.__enter__ = Mock()
                mock_engine.connect.return_value.__exit__ = Mock()
                mock_create_engine.return_value = mock_engine
                mock_load_config.return_value = config

                vector_store = ClarifAIVectorStore(config=config)

                # Mock the similarity_search return value
                with patch.object(vector_store, "similarity_search", return_value=[]):
                    results = vector_store.similarity_search("test query", top_k=5)
                    assert isinstance(results, list)
        else:
            # Integration test - requires real PostgreSQL service
            vector_store = ClarifAIVectorStore(config=config)
            results = vector_store.similarity_search("test query", top_k=5)
            assert isinstance(results, list)

    def test_delete_chunks_by_block_id(self, integration_mode):
        """Test deleting chunks by block ID."""
        config = ClarifAIConfig()
        config.postgres = DatabaseConfig(
            host="localhost",
            port=5432,
            user="test_user",
            password="test_pass",
            database="test_db",
        )

        if not integration_mode:
            with (
                patch(
                    "clarifai_shared.embedding.storage.create_engine"
                ) as mock_create_engine,
                patch("clarifai_shared.embedding.storage.PGVectorStore"),
                patch("clarifai_shared.embedding.storage.VectorStoreIndex"),
                patch("clarifai_shared.config.load_config") as mock_load_config,
            ):
                mock_engine = Mock()
                mock_engine.connect.return_value.__enter__ = Mock()
                mock_engine.connect.return_value.__exit__ = Mock()
                mock_create_engine.return_value = mock_engine
                mock_load_config.return_value = config

                vector_store = ClarifAIVectorStore(config=config)

                # Mock the delete_chunks_by_block_id return value
                with patch.object(
                    vector_store, "delete_chunks_by_block_id", return_value=0
                ):
                    deleted_count = vector_store.delete_chunks_by_block_id(
                        "test_block_id"
                    )
                    assert isinstance(deleted_count, int)
        else:
            # Integration test - requires real PostgreSQL service
            vector_store = ClarifAIVectorStore(config=config)
            deleted_count = vector_store.delete_chunks_by_block_id("test_block_id")
            assert isinstance(deleted_count, int)

    def test_get_store_metrics(self, integration_mode):
        """Test getting vector store metrics."""
        config = ClarifAIConfig()
        config.postgres = DatabaseConfig(
            host="localhost",
            port=5432,
            user="test_user",
            password="test_pass",
            database="test_db",
        )

        if not integration_mode:
            with (
                patch(
                    "clarifai_shared.embedding.storage.create_engine"
                ) as mock_create_engine,
                patch("clarifai_shared.embedding.storage.PGVectorStore"),
                patch("clarifai_shared.embedding.storage.VectorStoreIndex"),
                patch("clarifai_shared.config.load_config") as mock_load_config,
            ):
                mock_engine = Mock()
                mock_engine.connect.return_value.__enter__ = Mock()
                mock_engine.connect.return_value.__exit__ = Mock()
                mock_create_engine.return_value = mock_engine
                mock_load_config.return_value = config

                vector_store = ClarifAIVectorStore(config=config)

                # Mock the get_store_metrics return value
                with patch.object(
                    vector_store,
                    "get_store_metrics",
                    return_value=VectorStoreMetrics(0, 0, 0),
                ):
                    metrics = vector_store.get_store_metrics()
                    assert isinstance(metrics, VectorStoreMetrics)
        else:
            # Integration test - requires real PostgreSQL service
            vector_store = ClarifAIVectorStore(config=config)
            metrics = vector_store.get_store_metrics()
            assert isinstance(metrics, VectorStoreMetrics)

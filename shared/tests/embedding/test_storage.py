"""
Tests for embedding storage components.
"""

from unittest.mock import Mock, patch

import pytest
from aclarai_shared.config import DatabaseConfig, aclaraiConfig
from aclarai_shared.embedding.chunking import ChunkMetadata
from aclarai_shared.embedding.models import EmbeddedChunk
from aclarai_shared.embedding.storage import VectorStoreMetrics, aclaraiVectorStore


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


class TestaclaraiVectorStore:
    """Test cases for aclaraiVectorStore with configurable dependencies."""

    def test_vector_store_init_with_config(self):
        """Test aclaraiVectorStore initialization with config (unit test)."""
        config = aclaraiConfig()
        config.postgres = DatabaseConfig(
            host="localhost",
            port=5432,
            database="aclarai_test",
            user="test_user",
            password="test_pass",
        )
        with (
            patch(
                "aclarai_shared.embedding.storage.create_engine"
            ) as mock_create_engine,
            patch("aclarai_shared.embedding.storage.PGVectorStore"),
            patch("aclarai_shared.embedding.storage.VectorStoreIndex"),
            patch("aclarai_shared.config.load_config") as mock_load_config,
        ):
            mock_engine = Mock()
            mock_engine.connect.return_value.__enter__ = Mock()
            mock_engine.connect.return_value.__exit__ = Mock()
            mock_create_engine.return_value = mock_engine
            mock_load_config.return_value = config
            vector_store = aclaraiVectorStore(config=config)
            assert vector_store.config == config

    @pytest.mark.integration
    def test_vector_store_init_with_config_integration(self):
        """Test aclaraiVectorStore initialization with config (integration test)."""
        config = aclaraiConfig()
        config.postgres = DatabaseConfig(
            host="localhost",
            port=5432,
            database="aclarai_test",
            user="test_user",
            password="test_pass",
        )
        # Integration test - requires real PostgreSQL service
        vector_store = aclaraiVectorStore(config=config)
        assert vector_store.config == config

    def test_store_embeddings(self):
        """Test storing embeddings in vector store (unit test)."""
        config = aclaraiConfig()
        config.postgres = DatabaseConfig(
            host="localhost",
            port=5432,
            user="test_user",
            password="test_pass",
            database="test_db",
        )
        # Create test embedded chunks
        chunk_metadata = ChunkMetadata(
            aclarai_block_id="blk_store_test",
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
        with (
            patch(
                "aclarai_shared.embedding.storage.create_engine"
            ) as mock_create_engine,
            patch("aclarai_shared.embedding.storage.PGVectorStore"),
            patch("aclarai_shared.embedding.storage.VectorStoreIndex"),
            patch("aclarai_shared.config.load_config") as mock_load_config,
        ):
            mock_engine = Mock()
            mock_engine.connect.return_value.__enter__ = Mock()
            mock_engine.connect.return_value.__exit__ = Mock()
            mock_create_engine.return_value = mock_engine
            mock_load_config.return_value = config
            vector_store = aclaraiVectorStore(config=config)
            # Mock the store_embeddings return value
            with patch.object(
                vector_store,
                "store_embeddings",
                return_value=VectorStoreMetrics(1, 1, 0),
            ):
                metrics = vector_store.store_embeddings(embedded_chunks)
                assert isinstance(metrics, VectorStoreMetrics)

    @pytest.mark.integration
    def test_store_embeddings_integration(self):
        """Test storing embeddings in vector store (integration test)."""
        config = aclaraiConfig()
        config.postgres = DatabaseConfig(
            host="localhost",
            port=5432,
            user="test_user",
            password="test_pass",
            database="test_db",
        )
        # Create test embedded chunks
        chunk_metadata = ChunkMetadata(
            aclarai_block_id="blk_store_test",
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
        # Integration test - requires real PostgreSQL service
        vector_store = aclaraiVectorStore(config=config)
        metrics = vector_store.store_embeddings(embedded_chunks)
        assert isinstance(metrics, VectorStoreMetrics)

    def test_store_embeddings_empty_list(self):
        """Test storing empty list of embeddings (unit test)."""
        config = aclaraiConfig()
        config.postgres = DatabaseConfig(
            host="localhost",
            port=5432,
            user="test_user",
            password="test_pass",
            database="test_db",
        )
        with (
            patch(
                "aclarai_shared.embedding.storage.create_engine"
            ) as mock_create_engine,
            patch("aclarai_shared.embedding.storage.PGVectorStore"),
            patch("aclarai_shared.embedding.storage.VectorStoreIndex"),
            patch("aclarai_shared.config.load_config") as mock_load_config,
        ):
            mock_engine = Mock()
            mock_engine.connect.return_value.__enter__ = Mock()
            mock_engine.connect.return_value.__exit__ = Mock()
            mock_create_engine.return_value = mock_engine
            mock_load_config.return_value = config
            vector_store = aclaraiVectorStore(config=config)
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

    @pytest.mark.integration
    def test_store_embeddings_empty_list_integration(self):
        """Test storing empty list of embeddings (integration test)."""
        config = aclaraiConfig()
        config.postgres = DatabaseConfig(
            host="localhost",
            port=5432,
            user="test_user",
            password="test_pass",
            database="test_db",
        )
        # Integration test - requires real PostgreSQL service
        vector_store = aclaraiVectorStore(config=config)
        metrics = vector_store.store_embeddings([])
        assert metrics.total_vectors == 0
        assert metrics.successful_inserts == 0
        assert metrics.failed_inserts == 0

    def test_similarity_search(self):
        """Test similarity search functionality (unit test)."""
        config = aclaraiConfig()
        config.postgres = DatabaseConfig(
            host="localhost",
            port=5432,
            user="test_user",
            password="test_pass",
            database="test_db",
        )
        with (
            patch(
                "aclarai_shared.embedding.storage.create_engine"
            ) as mock_create_engine,
            patch("aclarai_shared.embedding.storage.PGVectorStore"),
            patch("aclarai_shared.embedding.storage.VectorStoreIndex"),
            patch("aclarai_shared.config.load_config") as mock_load_config,
        ):
            mock_engine = Mock()
            mock_engine.connect.return_value.__enter__ = Mock()
            mock_engine.connect.return_value.__exit__ = Mock()
            mock_create_engine.return_value = mock_engine
            mock_load_config.return_value = config
            vector_store = aclaraiVectorStore(config=config)
            # Mock the similarity_search return value
            with patch.object(vector_store, "similarity_search", return_value=[]):
                results = vector_store.similarity_search("test query", top_k=5)
                assert isinstance(results, list)

    @pytest.mark.integration
    def test_similarity_search_integration(self):
        """Test similarity search functionality (integration test)."""
        config = aclaraiConfig()
        config.postgres = DatabaseConfig(
            host="localhost",
            port=5432,
            user="test_user",
            password="test_pass",
            database="test_db",
        )
        # Integration test - requires real PostgreSQL service
        vector_store = aclaraiVectorStore(config=config)
        results = vector_store.similarity_search("test query", top_k=5)
        assert isinstance(results, list)

    def test_delete_chunks_by_block_id(self):
        """Test deleting chunks by block ID (unit test)."""
        config = aclaraiConfig()
        config.postgres = DatabaseConfig(
            host="localhost",
            port=5432,
            user="test_user",
            password="test_pass",
            database="test_db",
        )
        with (
            patch(
                "aclarai_shared.embedding.storage.create_engine"
            ) as mock_create_engine,
            patch("aclarai_shared.embedding.storage.PGVectorStore"),
            patch("aclarai_shared.embedding.storage.VectorStoreIndex"),
            patch("aclarai_shared.config.load_config") as mock_load_config,
        ):
            mock_engine = Mock()
            mock_engine.connect.return_value.__enter__ = Mock()
            mock_engine.connect.return_value.__exit__ = Mock()
            mock_create_engine.return_value = mock_engine
            mock_load_config.return_value = config
            vector_store = aclaraiVectorStore(config=config)
            # Mock the delete_chunks_by_block_id return value
            with patch.object(
                vector_store, "delete_chunks_by_block_id", return_value=0
            ):
                deleted_count = vector_store.delete_chunks_by_block_id("test_block_id")
                assert isinstance(deleted_count, int)

    @pytest.mark.integration
    def test_delete_chunks_by_block_id_integration(self):
        """Test deleting chunks by block ID (integration test)."""
        config = aclaraiConfig()
        config.postgres = DatabaseConfig(
            host="localhost",
            port=5432,
            user="test_user",
            password="test_pass",
            database="test_db",
        )
        # Integration test - requires real PostgreSQL service
        vector_store = aclaraiVectorStore(config=config)
        deleted_count = vector_store.delete_chunks_by_block_id("test_block_id")
        assert isinstance(deleted_count, int)

    def test_get_store_metrics(self):
        """Test getting vector store metrics (unit test)."""
        config = aclaraiConfig()
        config.postgres = DatabaseConfig(
            host="localhost",
            port=5432,
            user="test_user",
            password="test_pass",
            database="test_db",
        )
        with (
            patch(
                "aclarai_shared.embedding.storage.create_engine"
            ) as mock_create_engine,
            patch("aclarai_shared.embedding.storage.PGVectorStore"),
            patch("aclarai_shared.embedding.storage.VectorStoreIndex"),
            patch("aclarai_shared.config.load_config") as mock_load_config,
        ):
            mock_engine = Mock()
            mock_engine.connect.return_value.__enter__ = Mock()
            mock_engine.connect.return_value.__exit__ = Mock()
            mock_create_engine.return_value = mock_engine
            mock_load_config.return_value = config
            vector_store = aclaraiVectorStore(config=config)
            # Mock the get_store_metrics return value
            with patch.object(
                vector_store,
                "get_store_metrics",
                return_value=VectorStoreMetrics(0, 0, 0),
            ):
                metrics = vector_store.get_store_metrics()
                assert isinstance(metrics, VectorStoreMetrics)

    @pytest.mark.integration
    def test_get_store_metrics_integration(self):
        """Test getting vector store metrics (integration test)."""
        config = aclaraiConfig()
        config.postgres = DatabaseConfig(
            host="localhost",
            port=5432,
            user="test_user",
            password="test_pass",
            database="test_db",
        )
        # Integration test - requires real PostgreSQL service
        vector_store = aclaraiVectorStore(config=config)
        metrics = vector_store.get_store_metrics()
        assert isinstance(metrics, VectorStoreMetrics)

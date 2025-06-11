"""
Test to verify the OpenAI embedding dependency fix.

This test ensures that ClarifAIVectorStore can be created without
requiring the llama-index-embeddings-openai package.
"""

import pytest
from unittest.mock import patch, MagicMock
from clarifai_shared.config import ClarifAIConfig, DatabaseConfig
from clarifai_shared.embedding.storage import ClarifAIVectorStore, VectorStoreMetrics
from clarifai_shared.embedding.chunking import ChunkMetadata
from clarifai_shared.embedding.models import EmbeddedChunk
from llama_index.core.embeddings import BaseEmbedding


class TestOpenAIDependencyFix:
    """Test that ClarifAIVectorStore doesn't require OpenAI embeddings package."""

    def test_vector_store_creation_without_openai_package(self):
        """Test creating ClarifAIVectorStore without OpenAI dependency."""
        
        # Create test config
        config = ClarifAIConfig()
        config.database = DatabaseConfig(
            host="localhost",
            port=5432,
            user="test_user",
            password="test_pass",
            database="test_db",
        )

        # Mock external dependencies to focus on the OpenAI import issue
        with patch("clarifai_shared.embedding.storage.create_engine") as mock_engine, \
             patch("clarifai_shared.embedding.storage.PGVectorStore") as mock_pgvector, \
             patch("clarifai_shared.embedding.models.HuggingFaceEmbedding") as mock_hf_embedding:
            
            # Setup mocks
            mock_engine.return_value = MagicMock()
            mock_pgvector.from_params.return_value = MagicMock()
            
            # Create a proper mock embedding model that extends BaseEmbedding
            class MockEmbedding(BaseEmbedding):
                def _get_query_embedding(self, query: str):
                    return [0.1, 0.2, 0.3]
                
                def _get_text_embedding(self, text: str):
                    return [0.1, 0.2, 0.3]
                    
                async def _aget_query_embedding(self, query: str):
                    return [0.1, 0.2, 0.3]
                    
                async def _aget_text_embedding(self, text: str):
                    return [0.1, 0.2, 0.3]
            
            mock_embedding_instance = MockEmbedding()
            mock_hf_embedding.return_value = mock_embedding_instance
            
            # Mock the database connection methods
            mock_connection = MagicMock()
            mock_engine.return_value.connect.return_value.__enter__.return_value = mock_connection
            
            # This should NOT raise ImportError about llama-index-embeddings-openai
            vector_store = ClarifAIVectorStore(config=config)
            
            # Verify the vector store was created successfully
            assert vector_store is not None
            assert vector_store.embedding_generator is not None
            assert vector_store.vector_index is not None

    def test_store_embeddings_without_openai_package(self):
        """Test the store_embeddings method that was mentioned in the issue."""
        
        # Create test config exactly as in the failing test
        config = ClarifAIConfig()
        config.database = DatabaseConfig(
            host="localhost",
            port=5432,
            user="test_user",
            password="test_pass",
            database="test_db",
        )

        # Create test embedded chunks as in the failing test
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

        # Mock all external dependencies
        with patch("clarifai_shared.embedding.storage.create_engine") as mock_engine, \
             patch("clarifai_shared.embedding.storage.PGVectorStore") as mock_pgvector, \
             patch("clarifai_shared.embedding.models.HuggingFaceEmbedding") as mock_hf_embedding:
            
            # Setup mocks
            mock_engine.return_value = MagicMock()
            mock_pgvector.from_params.return_value = MagicMock()
            
            # Create a proper mock embedding model
            class MockEmbedding(BaseEmbedding):
                def _get_query_embedding(self, query: str):
                    return [0.1, 0.2, 0.3]
                
                def _get_text_embedding(self, text: str):
                    return [0.1, 0.2, 0.3]
                    
                async def _aget_query_embedding(self, query: str):
                    return [0.1, 0.2, 0.3]
                    
                async def _aget_text_embedding(self, text: str):
                    return [0.1, 0.2, 0.3]
            
            mock_embedding_instance = MockEmbedding()
            mock_hf_embedding.return_value = mock_embedding_instance
            
            # Mock the database connection methods
            mock_connection = MagicMock()
            mock_engine.return_value.connect.return_value.__enter__.return_value = mock_connection
            
            # Mock the vector index insert method
            mock_vector_index = MagicMock()
            
            # This should NOT raise ImportError about llama-index-embeddings-openai
            vector_store = ClarifAIVectorStore(config=config)
            vector_store.vector_index = mock_vector_index
            
            # Test the store_embeddings method that was failing
            metrics = vector_store.store_embeddings(embedded_chunks)
            
            # Verify the operation completed successfully
            assert isinstance(metrics, VectorStoreMetrics)
            assert metrics.total_vectors == 1
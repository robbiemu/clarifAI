"""
Tests for embedding module initialization and basic imports.
"""

import sys
from unittest.mock import Mock

# Mock all problematic dependencies before any imports
def setup_comprehensive_mocks():
    """Set up comprehensive mocks for heavy dependencies."""
    # Mock all llama_index modules
    mock_llm = Mock()
    mock_openai = Mock()
    mock_sentence_splitter = Mock()
    mock_vector_store_index = Mock()
    mock_storage_context = Mock()
    mock_service_context = Mock()
    
    # Core llama_index mocks
    sys.modules['llama_index'] = Mock()
    sys.modules['llama_index.core'] = Mock()
    sys.modules['llama_index.core.llms'] = Mock()
    sys.modules['llama_index.core.llms'].LLM = mock_llm
    sys.modules['llama_index.llms'] = Mock()
    sys.modules['llama_index.llms.openai'] = Mock()
    sys.modules['llama_index.llms.openai'].OpenAI = mock_openai
    
    # Embedding-specific mocks
    sys.modules['llama_index.embeddings'] = Mock()
    sys.modules['llama_index.embeddings.base'] = Mock()
    sys.modules['llama_index.embeddings.huggingface'] = Mock()
    sys.modules['llama_index.core.embeddings'] = Mock()
    sys.modules['llama_index.core.embeddings.base'] = Mock()
    
    # Vector store mocks
    sys.modules['llama_index.vector_stores'] = Mock()
    sys.modules['llama_index.vector_stores.postgres'] = Mock()
    sys.modules['llama_index.core.vector_stores'] = Mock()
    sys.modules['llama_index.core.vector_stores.types'] = Mock()
    
    # Index and storage mocks
    sys.modules['llama_index.core.indices'] = Mock()
    sys.modules['llama_index.core.storage'] = Mock()
    sys.modules['llama_index.core.storage.storage_context'] = Mock()
    sys.modules['llama_index.core.indices.vector_store'] = Mock()
    sys.modules['llama_index.core.indices.vector_store'].VectorStoreIndex = mock_vector_store_index
    
    # Schema and node parser mocks
    sys.modules['llama_index.core.schema'] = Mock()
    sys.modules['llama_index.core.node_parser'] = Mock()
    sys.modules['llama_index.core.node_parser'].SentenceSplitter = mock_sentence_splitter
    
    # External library mocks
    sys.modules['hnswlib'] = Mock()
    sys.modules['sentence_transformers'] = Mock()
    sys.modules['psycopg2'] = Mock()
    sys.modules['psycopg2.extensions'] = Mock()
    sys.modules['pgvector'] = Mock()
    sys.modules['sqlalchemy'] = Mock()
    
    # Neo4j mocks
    neo4j_mock = Mock()
    neo4j_exceptions_mock = Mock()
    neo4j_exceptions_mock.ServiceUnavailable = Exception
    neo4j_exceptions_mock.AuthError = Exception  
    neo4j_exceptions_mock.TransientError = Exception
    
    sys.modules['neo4j'] = neo4j_mock
    sys.modules['neo4j.exceptions'] = neo4j_exceptions_mock
    neo4j_mock.exceptions = neo4j_exceptions_mock
    neo4j_mock.GraphDatabase = Mock()

# Set up mocks before importing
setup_comprehensive_mocks()

# Add shared directory to sys.path to enable imports
sys.path.insert(0, '/home/runner/work/clarifAI/clarifAI/shared')

# Now we can import the embedding modules
from clarifai_shared.embedding import (
    UtteranceChunker, 
    ChunkMetadata, 
    EmbeddingGenerator, 
    EmbeddedChunk,
    ClarifAIVectorStore,
    VectorStoreMetrics
)


class TestEmbeddingInit:
    """Test that embedding module components can be imported and instantiated."""
    
    def test_utterance_chunker_import(self):
        """Test UtteranceChunker can be imported."""
        assert UtteranceChunker is not None
        assert hasattr(UtteranceChunker, '__name__')
    
    def test_chunk_metadata_import(self):
        """Test ChunkMetadata can be imported."""
        assert ChunkMetadata is not None
        assert hasattr(ChunkMetadata, '__name__')
    
    def test_embedding_generator_import(self):
        """Test EmbeddingGenerator can be imported."""
        assert EmbeddingGenerator is not None
        assert hasattr(EmbeddingGenerator, '__name__')
    
    def test_embedded_chunk_import(self):
        """Test EmbeddedChunk can be imported."""
        assert EmbeddedChunk is not None
        assert hasattr(EmbeddedChunk, '__name__')
    
    def test_vector_store_import(self):
        """Test ClarifAIVectorStore can be imported."""
        assert ClarifAIVectorStore is not None
        assert hasattr(ClarifAIVectorStore, '__name__')
    
    def test_vector_store_metrics_import(self):
        """Test VectorStoreMetrics can be imported."""
        assert VectorStoreMetrics is not None
        assert hasattr(VectorStoreMetrics, '__name__')
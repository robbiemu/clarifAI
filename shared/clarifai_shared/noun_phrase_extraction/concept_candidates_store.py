"""
Vector storage for concept candidates.

This module provides specialized vector storage for concept candidates extracted
from Claims and Summary nodes, implementing the concept_candidates vector table
as specified in docs/arch/on-vector_stores.md.
"""

import logging
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass

from llama_index.core import VectorStoreIndex, Settings, Document
from llama_index.vector_stores.postgres import PGVectorStore
from sqlalchemy import create_engine

from ..config import ClarifAIConfig
from ..embedding import EmbeddingGenerator
from .models import NounPhraseCandidate

logger = logging.getLogger(__name__)


@dataclass
class ConceptCandidateDocument:
    """Document wrapper for concept candidates in vector storage."""
    
    doc_id: str
    text: str  # Normalized text that gets embedded
    metadata: Dict[str, Any]  # All candidate metadata
    embedding: Optional[List[float]] = None


class ConceptCandidatesVectorStore:
    """
    Specialized vector store for concept candidates.
    
    This store manages the concept_candidates vector table specifically for
    noun phrases extracted from Claims and Summary nodes, following the
    architecture from docs/arch/on-concepts.md.
    """
    
    def __init__(self, config: Optional[ClarifAIConfig] = None):
        """
        Initialize the concept candidates vector store.
        
        Args:
            config: ClarifAI configuration (loads default if None)
        """
        if config is None:
            from ..config import load_config
            config = load_config(validate=True)
        
        self.config = config
        
        # Use the concept_candidates collection configuration
        self.collection_name = config.noun_phrase_extraction.concept_candidates_collection
        self.embed_dim = config.noun_phrase_extraction.embed_dim
        
        # Build connection string
        self.connection_string = config.postgres.get_connection_url(
            "postgresql+psycopg2"
        )
        
        # Initialize database engine
        self.engine = create_engine(
            self.connection_string,
            pool_pre_ping=True,
            pool_recycle=3600,
            echo=config.debug,
        )
        
        # Initialize PGVectorStore for concept_candidates
        self.vector_store = self._initialize_pgvector_store()
        
        # Initialize embedding generator
        self.embedding_generator = EmbeddingGenerator(config=config)
        
        # Set LlamaIndex embedding model
        Settings.embed_model = self.embedding_generator.embedding_model
        
        # Initialize VectorStoreIndex
        self.vector_index = VectorStoreIndex.from_vector_store(
            self.vector_store, embed_model=self.embedding_generator.embedding_model
        )
        
        logger.info(
            f"Initialized ConceptCandidatesVectorStore with collection: {self.collection_name}, "
            f"dimension: {self.embed_dim}",
            extra={
                "service": "clarifai",
                "filename.function_name": "concept_candidates_vector_store.ConceptCandidatesVectorStore.__init__",
                "collection_name": self.collection_name,
                "embed_dim": self.embed_dim,
            }
        )
    
    def store_candidates(self, candidates: List[NounPhraseCandidate]) -> int:
        """
        Store noun phrase candidates in the vector database.
        
        Args:
            candidates: List of NounPhraseCandidate objects to store
            
        Returns:
            Number of candidates successfully stored
        """
        if not candidates:
            logger.warning(
                "No candidates provided for storage",
                extra={
                    "service": "clarifai",
                    "filename.function_name": "concept_candidates_vector_store.ConceptCandidatesVectorStore.store_candidates",
                }
            )
            return 0
        
        logger.info(
            f"Storing {len(candidates)} concept candidates in vector store",
            extra={
                "service": "clarifai",
                "filename.function_name": "concept_candidates_vector_store.ConceptCandidatesVectorStore.store_candidates",
                "candidates_count": len(candidates),
            }
        )
        
        try:
            # Convert candidates to documents
            documents = self._convert_candidates_to_documents(candidates)
            
            # Generate embeddings if not already present
            for i, candidate in enumerate(candidates):
                if candidate.embedding is None:
                    # Generate embedding for normalized text
                    embedding = self.embedding_generator.generate_embeddings([candidate.normalized_text])[0]
                    candidate.embedding = embedding
                    documents[i].embedding = embedding
                else:
                    documents[i].embedding = candidate.embedding
            
            # Store documents in vector index
            successful_count = 0
            for doc in documents:
                try:
                    self.vector_index.insert(doc)
                    successful_count += 1
                except Exception as e:
                    logger.error(
                        f"Failed to insert candidate document {doc.doc_id}",
                        extra={
                            "service": "clarifai",
                            "filename.function_name": "concept_candidates_vector_store.ConceptCandidatesVectorStore.store_candidates",
                            "doc_id": doc.doc_id,
                            "error": str(e),
                        }
                    )
            
            logger.info(
                f"Successfully stored {successful_count}/{len(candidates)} concept candidates",
                extra={
                    "service": "clarifai",
                    "filename.function_name": "concept_candidates_vector_store.ConceptCandidatesVectorStore.store_candidates",
                    "successful_count": successful_count,
                    "total_count": len(candidates),
                }
            )
            
            return successful_count
            
        except Exception as e:
            logger.error(
                f"Failed to store concept candidates: {e}",
                extra={
                    "service": "clarifai",
                    "filename.function_name": "concept_candidates_vector_store.ConceptCandidatesVectorStore.store_candidates",
                    "candidates_count": len(candidates),
                    "error": str(e),
                }
            )
            return 0
    
    def find_similar_candidates(
        self, 
        query_text: str, 
        top_k: int = 10,
        similarity_threshold: Optional[float] = None
    ) -> List[Tuple[Dict[str, Any], float]]:
        """
        Find similar concept candidates using vector similarity.
        
        Args:
            query_text: Text to search for similar candidates
            top_k: Number of results to return
            similarity_threshold: Minimum similarity score
            
        Returns:
            List of (metadata, similarity_score) tuples
        """
        logger.debug(
            f"Searching for similar concept candidates: query='{query_text[:50]}...', top_k={top_k}",
            extra={
                "service": "clarifai",
                "filename.function_name": "concept_candidates_vector_store.ConceptCandidatesVectorStore.find_similar_candidates",
                "query_length": len(query_text),
                "top_k": top_k,
            }
        )
        
        try:
            # Use VectorStoreIndex for similarity search
            query_engine = self.vector_index.as_query_engine(
                similarity_top_k=top_k,
                response_mode="no_text",
            )
            
            response = query_engine.query(query_text)
            
            results = []
            if hasattr(response, "source_nodes"):
                for node in response.source_nodes:
                    metadata = node.node.metadata
                    score = getattr(node, "score", 0.0)
                    
                    # Apply similarity threshold if specified
                    if similarity_threshold is None or score >= similarity_threshold:
                        results.append((metadata, score))
            
            logger.debug(
                f"Found {len(results)} similar concept candidates",
                extra={
                    "service": "clarifai",
                    "filename.function_name": "concept_candidates_vector_store.ConceptCandidatesVectorStore.find_similar_candidates",
                    "results_count": len(results),
                }
            )
            
            return results
            
        except Exception as e:
            logger.error(
                f"Failed to find similar concept candidates: {e}",
                extra={
                    "service": "clarifai",
                    "filename.function_name": "concept_candidates_vector_store.ConceptCandidatesVectorStore.find_similar_candidates",
                    "error": str(e),
                }
            )
            return []
    
    def get_candidates_by_status(self, status: str) -> List[Dict[str, Any]]:
        """
        Retrieve all candidates with a specific status (e.g., "pending").
        
        Args:
            status: Status to filter by
            
        Returns:
            List of candidate metadata dictionaries
        """
        logger.debug(
            f"Retrieving candidates with status: {status}",
            extra={
                "service": "clarifai",
                "filename.function_name": "concept_candidates_vector_store.ConceptCandidatesVectorStore.get_candidates_by_status",
                "status": status,
            }
        )
        
        try:
            # Use similarity search with empty query but metadata filter
            results = self.find_similar_candidates(
                query_text="",  # Empty query to get all
                top_k=1000,  # Large number to get all matches
            )
            
            # Filter by status
            filtered_results = [
                metadata for metadata, score in results
                if metadata.get("status") == status
            ]
            
            logger.debug(
                f"Found {len(filtered_results)} candidates with status '{status}'",
                extra={
                    "service": "clarifai",
                    "filename.function_name": "concept_candidates_vector_store.ConceptCandidatesVectorStore.get_candidates_by_status",
                    "status": status,
                    "count": len(filtered_results),
                }
            )
            
            return filtered_results
            
        except Exception as e:
            logger.error(
                f"Failed to retrieve candidates by status '{status}': {e}",
                extra={
                    "service": "clarifai",
                    "filename.function_name": "concept_candidates_vector_store.ConceptCandidatesVectorStore.get_candidates_by_status",
                    "status": status,
                    "error": str(e),
                }
            )
            return []
    
    def _initialize_pgvector_store(self) -> PGVectorStore:
        """Initialize PGVectorStore for concept_candidates collection."""
        try:
            # Ensure pgvector extension is enabled
            self._ensure_pgvector_extension()
            
            # Initialize PGVectorStore with concept_candidates collection
            vector_store = PGVectorStore.from_params(
                database=self.config.postgres.database,
                host=self.config.postgres.host,
                password=self.config.postgres.password,
                port=self.config.postgres.port,
                user=self.config.postgres.user,
                table_name=self.collection_name,
                embed_dim=self.embed_dim,
                hnsw_kwargs={
                    "hnsw_m": 16,
                    "hnsw_ef_construction": 64,
                    "hnsw_ef_search": 40,
                },
            )
            
            logger.info(
                f"Initialized PGVectorStore for concept_candidates: {self.collection_name}",
                extra={
                    "service": "clarifai",
                    "filename.function_name": "concept_candidates_vector_store.ConceptCandidatesVectorStore._initialize_pgvector_store",
                    "table_name": self.collection_name,
                }
            )
            
            return vector_store
            
        except Exception as e:
            logger.error(
                f"Failed to initialize PGVectorStore for concept_candidates: {e}",
                extra={
                    "service": "clarifai",
                    "filename.function_name": "concept_candidates_vector_store.ConceptCandidatesVectorStore._initialize_pgvector_store",
                    "error": str(e),
                }
            )
            raise
    
    def _ensure_pgvector_extension(self):
        """Ensure the pgvector extension is enabled in PostgreSQL."""
        try:
            from sqlalchemy import text
            
            with self.engine.connect() as conn:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                conn.commit()
                
            logger.debug(
                "Ensured pgvector extension is enabled",
                extra={
                    "service": "clarifai",
                    "filename.function_name": "concept_candidates_vector_store.ConceptCandidatesVectorStore._ensure_pgvector_extension",
                }
            )
        except Exception as e:
            logger.error(
                f"Failed to enable pgvector extension: {e}",
                extra={
                    "service": "clarifai",
                    "filename.function_name": "concept_candidates_vector_store.ConceptCandidatesVectorStore._ensure_pgvector_extension",
                    "error": str(e),
                }
            )
            raise
    
    def _convert_candidates_to_documents(
        self, 
        candidates: List[NounPhraseCandidate]
    ) -> List[Document]:
        """
        Convert NounPhraseCandidate objects to LlamaIndex Documents.
        
        Args:
            candidates: List of candidates to convert
            
        Returns:
            List of Document objects for LlamaIndex
        """
        documents = []
        
        for candidate in candidates:
            # Create comprehensive metadata
            metadata = {
                "original_text": candidate.text,
                "normalized_text": candidate.normalized_text,
                "source_node_id": candidate.source_node_id,
                "source_node_type": candidate.source_node_type,
                "clarifai_id": candidate.clarifai_id,
                "status": candidate.status,
                "timestamp": candidate.timestamp.isoformat() if candidate.timestamp else None,
            }
            
            # Create Document with normalized text as the content
            doc = Document(
                text=candidate.normalized_text,  # This is what gets embedded and searched
                metadata=metadata,
                doc_id=f"{candidate.source_node_type}_{candidate.source_node_id}_{candidate.text[:50]}",
                embedding=candidate.embedding,
            )
            
            documents.append(doc)
        
        return documents
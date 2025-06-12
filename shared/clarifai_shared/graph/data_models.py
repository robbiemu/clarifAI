"""
Data models for Neo4j graph operations.

Defines input types for creating nodes and relationships in the knowledge graph.
These models support the Claimify pipeline's output persistence to Neo4j.
"""

import logging
from dataclasses import dataclass
from typing import Optional, Union
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class GraphNodeInput:
    """
    Base class for graph node input data.
    
    Contains common properties for all node types that will be created in Neo4j.
    """
    
    id: str  # Unique identifier for the node
    text: str  # Text content
    block_id: str  # ID of the source block (for ORIGINATES_FROM relationship)
    version: int = 1  # Version number for the node
    timestamp: Optional[datetime] = None  # When the node was created
    
    def __post_init__(self):
        """Set default timestamp if not provided."""
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class ClaimInput(GraphNodeInput):
    """
    Input data for creating (:Claim) nodes in Neo4j.
    
    Based on the schema defined in graph_schema.cypher and the requirements
    from on-claim_generation.md for claim quality scores.
    """
    
    # Quality scores from evaluation agents (can be null initially)
    entailed_score: Optional[float] = None
    coverage_score: Optional[float] = None  
    decontextualization_score: Optional[float] = None
    
    # Claim quality properties
    verifiable: bool = True
    self_contained: bool = True
    context_complete: bool = True
    
    def to_neo4j_properties(self) -> dict:
        """Convert to Neo4j node properties dictionary."""
        return {
            "id": self.id,
            "text": self.text,
            "entailed_score": self.entailed_score,
            "coverage_score": self.coverage_score,
            "decontextualization_score": self.decontextualization_score,
            "verifiable": self.verifiable,
            "self_contained": self.self_contained,
            "context_complete": self.context_complete,
            "version": self.version,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }


@dataclass
class SentenceInput(GraphNodeInput):
    """
    Input data for creating (:Sentence) nodes in Neo4j.
    
    For sentences that didn't become claims due to failing Claimify criteria
    (ambiguous references, not atomic, not verifiable, etc.).
    """
    
    # Sentence quality flags
    ambiguous: bool = False
    verifiable: bool = False
    failed_decomposition: bool = False
    
    # Optional reason for not becoming a claim
    rejection_reason: Optional[str] = None
    
    def to_neo4j_properties(self) -> dict:
        """Convert to Neo4j node properties dictionary."""
        return {
            "id": self.id,
            "text": self.text,
            "ambiguous": self.ambiguous,
            "verifiable": self.verifiable,
            "failed_decomposition": self.failed_decomposition,
            "rejection_reason": self.rejection_reason,
            "version": self.version,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }


@dataclass 
class BlockNodeInput(GraphNodeInput):
    """
    Input data for creating (:Block) nodes in Neo4j.
    
    Represents Tier 1 markdown blocks that are the source of claims and sentences.
    """
    
    content_hash: Optional[str] = None
    source_file: Optional[str] = None
    needs_reprocessing: bool = False
    last_synced: Optional[datetime] = None
    
    def to_neo4j_properties(self) -> dict:
        """Convert to Neo4j node properties dictionary."""
        return {
            "id": self.id,
            "text": self.text,
            "content_hash": self.content_hash,
            "source_file": self.source_file,
            "needs_reprocessing": self.needs_reprocessing,
            "version": self.version,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "last_synced": self.last_synced.isoformat() if self.last_synced else None,
        }


# Type alias for any node input type
NodeInputType = Union[ClaimInput, SentenceInput, BlockNodeInput]
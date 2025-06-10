"""
Data models for ClarifAI knowledge graph nodes.

This module defines the data structures for Claims, Sentences, and other
graph entities, following the schema from technical_overview.md and
graph_schema.cypher.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any
import uuid


@dataclass
class ClaimInput:
    """Input data for creating a Claim node."""

    text: str
    block_id: str  # ID of the originating Block node
    entailed_score: Optional[float] = None
    coverage_score: Optional[float] = None
    decontextualization_score: Optional[float] = None
    claim_id: Optional[str] = None  # Will generate if not provided

    def __post_init__(self):
        """Generate claim_id if not provided."""
        if self.claim_id is None:
            self.claim_id = f"claim_{uuid.uuid4().hex[:12]}"


@dataclass
class SentenceInput:
    """Input data for creating a Sentence node."""

    text: str
    block_id: str  # ID of the originating Block node
    ambiguous: Optional[bool] = None
    verifiable: Optional[bool] = None
    sentence_id: Optional[str] = None  # Will generate if not provided

    def __post_init__(self):
        """Generate sentence_id if not provided."""
        if self.sentence_id is None:
            self.sentence_id = f"sentence_{uuid.uuid4().hex[:12]}"


@dataclass
class Claim:
    """Represents a Claim node in the knowledge graph."""

    claim_id: str
    text: str
    entailed_score: Optional[float]
    coverage_score: Optional[float]
    decontextualization_score: Optional[float]
    version: int
    timestamp: datetime

    @classmethod
    def from_input(cls, claim_input: ClaimInput, version: int = 1) -> "Claim":
        """Create a Claim from ClaimInput."""
        return cls(
            claim_id=claim_input.claim_id,
            text=claim_input.text,
            entailed_score=claim_input.entailed_score,
            coverage_score=claim_input.coverage_score,
            decontextualization_score=claim_input.decontextualization_score,
            version=version,
            timestamp=datetime.utcnow(),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Neo4j storage."""
        return {
            "id": self.claim_id,  # Use 'id' as primary key in Neo4j
            "text": self.text,
            "entailed_score": self.entailed_score,
            "coverage_score": self.coverage_score,
            "decontextualization_score": self.decontextualization_score,
            "version": self.version,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class Sentence:
    """Represents a Sentence node in the knowledge graph."""

    sentence_id: str
    text: str
    ambiguous: Optional[bool]
    verifiable: Optional[bool]
    version: int
    timestamp: datetime

    @classmethod
    def from_input(cls, sentence_input: SentenceInput, version: int = 1) -> "Sentence":
        """Create a Sentence from SentenceInput."""
        return cls(
            sentence_id=sentence_input.sentence_id,
            text=sentence_input.text,
            ambiguous=sentence_input.ambiguous,
            verifiable=sentence_input.verifiable,
            version=version,
            timestamp=datetime.utcnow(),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Neo4j storage."""
        return {
            "id": self.sentence_id,  # Use 'id' as primary key in Neo4j
            "text": self.text,
            "ambiguous": self.ambiguous,
            "verifiable": self.verifiable,
            "version": self.version,
            "timestamp": self.timestamp.isoformat(),
        }

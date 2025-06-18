"""
Data models for concept detection using hnswlib.

This module defines the data structures used for concept similarity detection
and the decision logic for merging vs promoting concept candidates.
"""

import logging
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum

logger = logging.getLogger(__name__)


class ConceptAction(Enum):
    """Actions that can be taken for a concept candidate."""

    MERGED = "merged"  # Candidate is similar to existing concept
    PROMOTED = "promoted"  # Candidate should become a new canonical concept


@dataclass
class SimilarityMatch:
    """
    Represents a similarity match between a candidate and existing concept.
    """

    candidate_id: str  # ID of the concept candidate
    matched_concept_id: Optional[str]  # ID of the matched canonical concept (if any)
    matched_candidate_id: Optional[str]  # ID of matched candidate (if any)
    similarity_score: float  # Cosine similarity score
    matched_text: str  # Text of the matched item
    metadata: Dict[str, Any] = field(default_factory=dict)  # Additional metadata


@dataclass
class ConceptDetectionResult:
    """
    Result of concept detection for a single candidate.

    Contains the recommended action and any similarity matches found.
    """

    candidate_id: str
    candidate_text: str
    action: ConceptAction
    similarity_matches: List[SimilarityMatch] = field(default_factory=list)
    confidence: float = 1.0  # Confidence in the decision
    reason: str = ""  # Human-readable explanation of the decision

    @property
    def best_match(self) -> Optional[SimilarityMatch]:
        """Get the best similarity match if any."""
        if not self.similarity_matches:
            return None
        return max(self.similarity_matches, key=lambda m: m.similarity_score)


@dataclass
class ConceptDetectionBatch:
    """
    Result of processing a batch of concept candidates.
    """

    results: List[ConceptDetectionResult] = field(default_factory=list)
    total_processed: int = 0
    merged_count: int = 0
    promoted_count: int = 0
    processing_time: Optional[float] = None
    error: Optional[str] = None

    @property
    def is_successful(self) -> bool:
        """Check if the batch processing was successful."""
        return self.error is None

    @property
    def merge_rate(self) -> float:
        """Calculate the rate of candidates that were merged."""
        if self.total_processed == 0:
            return 0.0
        return self.merged_count / self.total_processed

    @property
    def promotion_rate(self) -> float:
        """Calculate the rate of candidates that were promoted."""
        if self.total_processed == 0:
            return 0.0
        return self.promoted_count / self.total_processed

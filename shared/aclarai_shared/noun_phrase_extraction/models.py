"""
Data models for noun phrase extraction.

This module defines the data structures used for noun phrase extraction
and storage in the concept_candidates vector table.
"""

import logging
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


@dataclass
class NounPhraseCandidate:
    """
    Represents a noun phrase extracted from a Claim or Summary node.

    This corresponds to an entry that will be stored in the concept_candidates
    vector table with metadata for future deduplication and promotion.
    """

    text: str  # Original extracted noun phrase
    normalized_text: str  # Normalized version (lowercase, lemmatized, etc.)
    source_node_id: str  # ID of the Claim or Summary node this came from
    source_node_type: str  # "claim" or "summary"
    aclarai_id: str  # aclarai:id for traceability
    embedding: Optional[List[float]] = None  # Vector embedding of normalized text
    status: str = "pending"  # Status for future processing (always "pending" initially)
    timestamp: Optional[datetime] = None

    def __post_init__(self):
        """Set timestamp if not provided."""
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)


@dataclass
class ExtractionResult:
    """
    Result of noun phrase extraction from a batch of Claims and Summaries.

    Contains all extracted candidates and metadata about the processing.
    """

    candidates: List[NounPhraseCandidate] = field(default_factory=list)
    total_nodes_processed: int = 0
    total_phrases_extracted: int = 0
    successful_extractions: int = 0
    failed_extractions: int = 0
    processing_time: Optional[float] = None
    model_used: Optional[str] = None
    error: Optional[str] = None

    @property
    def is_successful(self) -> bool:
        """Check if the extraction was successful overall."""
        return self.error is None and self.failed_extractions == 0

    @property
    def success_rate(self) -> float:
        """Calculate the success rate of extractions."""
        if self.total_nodes_processed == 0:
            return 0.0
        return self.successful_extractions / self.total_nodes_processed

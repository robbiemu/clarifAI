"""
Data models for the Claimify pipeline.

Defines the core data structures used throughout the Selection → Disambiguation → Decomposition
pipeline, including input/output types and configuration models.
"""

import logging
from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class NodeType(str, Enum):
    """Types of nodes that can be created from processed content."""

    CLAIM = "Claim"
    SENTENCE = "Sentence"


@dataclass
class SentenceChunk:
    """
    A sentence chunk to be processed by the Claimify pipeline.

    Represents individual sentences extracted from Tier 1 content,
    which serve as input to the Selection stage.
    """

    text: str
    source_id: str  # Original block/document ID
    chunk_id: str  # Unique identifier for this chunk
    sentence_index: int  # Position within the source


@dataclass
class ClaimifyContext:
    """
    Context window for Claimify processing.

    Contains preceding and following sentences to provide context
    during Selection and Disambiguation stages.
    """

    current_sentence: SentenceChunk
    preceding_sentences: List[SentenceChunk] = field(
        default_factory=list
    )  # p sentences
    following_sentences: List[SentenceChunk] = field(
        default_factory=list
    )  # f sentences

    @property
    def context_window_size(self) -> tuple[int, int]:
        """Returns (p, f) context window size."""
        return len(self.preceding_sentences), len(self.following_sentences)


@dataclass
class SelectionResult:
    """Result of the Selection stage."""

    sentence_chunk: SentenceChunk
    is_selected: bool
    confidence: Optional[float] = None
    reasoning: Optional[str] = None
    processing_time: Optional[float] = None
    rewritten_text: Optional[str] = None  # Cleaned sentence text from LLM


@dataclass
class DisambiguationResult:
    """Result of the Disambiguation stage."""

    original_sentence: SentenceChunk
    disambiguated_text: str
    changes_made: List[str] = field(default_factory=list)  # Description of changes
    confidence: Optional[float] = None
    processing_time: Optional[float] = None


@dataclass
class ClaimCandidate:
    """A candidate claim from the Decomposition stage."""

    text: str
    is_atomic: bool
    is_self_contained: bool
    is_verifiable: bool
    confidence: Optional[float] = None
    reasoning: Optional[str] = None

    @property
    def passes_criteria(self) -> bool:
        """Check if the claim meets all Claimify criteria."""
        return self.is_atomic and self.is_self_contained and self.is_verifiable

    @property
    def node_type(self) -> NodeType:
        """Determine the appropriate node type for this candidate."""
        return NodeType.CLAIM if self.passes_criteria else NodeType.SENTENCE


@dataclass
class DecompositionResult:
    """Result of the Decomposition stage."""

    original_text: str
    claim_candidates: List[ClaimCandidate] = field(default_factory=list)
    processing_time: Optional[float] = None

    @property
    def valid_claims(self) -> List[ClaimCandidate]:
        """Get candidates that pass Claimify criteria."""
        return [claim for claim in self.claim_candidates if claim.passes_criteria]

    @property
    def sentence_nodes(self) -> List[ClaimCandidate]:
        """Get candidates that should become Sentence nodes."""
        return [claim for claim in self.claim_candidates if not claim.passes_criteria]


@dataclass
class ClaimifyResult:
    """Complete result of processing a sentence through the Claimify pipeline."""

    original_chunk: SentenceChunk
    context: ClaimifyContext
    selection_result: Optional[SelectionResult] = None
    disambiguation_result: Optional[DisambiguationResult] = None
    decomposition_result: Optional[DecompositionResult] = None
    total_processing_time: Optional[float] = None
    errors: List[str] = field(default_factory=list)

    @property
    def was_processed(self) -> bool:
        """Check if the sentence was selected for processing."""
        return self.selection_result is not None and self.selection_result.is_selected

    @property
    def final_claims(self) -> List[ClaimCandidate]:
        """Get the final valid claims from this processing."""
        if self.decomposition_result:
            return self.decomposition_result.valid_claims
        return []

    @property
    def final_sentences(self) -> List[ClaimCandidate]:
        """Get candidates that should become Sentence nodes."""
        if self.decomposition_result:
            return self.decomposition_result.sentence_nodes
        return []


@dataclass
class ClaimifyConfig:
    """Configuration for the Claimify pipeline."""

    # Context window parameters
    context_window_p: int = 3  # Previous sentences
    context_window_f: int = 1  # Following sentences

    # Model configuration
    selection_model: Optional[str] = None
    disambiguation_model: Optional[str] = None
    decomposition_model: Optional[str] = None
    default_model: str = "gpt-3.5-turbo"

    # Processing parameters
    max_retries: int = 3
    timeout_seconds: int = 30
    temperature: float = 0.1
    max_tokens: int = 1000

    # Quality thresholds (to be added when threshold evaluation is implemented)
    # selection_confidence_threshold: float = 0.5
    # disambiguation_confidence_threshold: float = 0.5
    # decomposition_confidence_threshold: float = 0.5

    # Logging configuration
    log_decisions: bool = True
    log_transformations: bool = True
    log_timing: bool = True

    def get_model_for_stage(self, stage: str) -> str:
        """Get the configured model for a specific pipeline stage."""
        stage_models = {
            "selection": self.selection_model,
            "disambiguation": self.disambiguation_model,
            "decomposition": self.decomposition_model,
        }
        return stage_models.get(stage) or self.default_model

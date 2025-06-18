"""
Noun phrase extraction module for aclarai.

This module implements noun phrase extraction from Claims and Summary nodes,
providing the foundation for concept detection and deduplication workflows.
"""

from .extractor import NounPhraseExtractor
from .models import NounPhraseCandidate, ExtractionResult
from .concept_candidates_store import ConceptCandidatesVectorStore

__all__ = [
    "NounPhraseExtractor",
    "NounPhraseCandidate",
    "ExtractionResult",
    "ConceptCandidatesVectorStore",
]

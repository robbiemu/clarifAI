"""
Noun phrase extraction module for ClarifAI.

This module implements noun phrase extraction from Claims and Summary nodes,
following the specifications in docs/project/epic_1/sprint_4-Create_noun_phrase_extractor.md
and architecture guidelines in docs/arch/on-noun_phrase_extraction.md.
"""

from .extractor import NounPhraseExtractor
from .models import NounPhraseCandidate, ExtractionResult

__all__ = [
    "NounPhraseExtractor",
    "NounPhraseCandidate", 
    "ExtractionResult",
]
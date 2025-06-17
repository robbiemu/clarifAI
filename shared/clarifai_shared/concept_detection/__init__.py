"""
Concept detection module using hnswlib for similarity-based concept deduplication.

This module provides functionality to detect similar concept candidates and
determine whether they should be merged with existing concepts or promoted
to new canonical concepts.
"""

from .detector import ConceptDetector
from .models import ConceptDetectionResult, SimilarityMatch

__all__ = ["ConceptDetector", "ConceptDetectionResult", "SimilarityMatch"]

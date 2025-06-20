"""
Claim-Concept Linking Module.
This module provides functionality to link (:Claim) nodes to (:Concept) nodes
using LLM-based classification, following the architecture defined in
docs/arch/on-linking_claims_to_concepts.md.
"""

from .agent import ClaimConceptLinkerAgent
from .markdown_updater import Tier2MarkdownUpdater
from .models import (
    AgentClassificationResult,
    ClaimConceptLinkResult,
    ClaimConceptPair,
    ConceptCandidate,
    LinkingError,
    RelationshipType,
)
from .neo4j_operations import ClaimConceptNeo4jManager
from .orchestrator import ClaimConceptLinker

__all__ = [
    "ClaimConceptLinkerAgent",
    "ClaimConceptPair",
    "ClaimConceptLinkResult",
    "RelationshipType",
    "LinkingError",
    "ConceptCandidate",
    "AgentClassificationResult",
    "ClaimConceptNeo4jManager",
    "Tier2MarkdownUpdater",
    "ClaimConceptLinker",
]

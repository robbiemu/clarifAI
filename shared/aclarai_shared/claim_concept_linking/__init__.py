"""
Claim-Concept Linking Module.

This module provides the orchestration logic for linking Claim nodes to Concept nodes
in the aclarai knowledge graph using LLM-based classification and vector similarity search.
"""

from .orchestrator import ClaimConceptLinker

# Import additional components if they exist
try:
    from .agent import ClaimConceptLinkerAgent
    from .models import (
        ClaimConceptPair,
        ClaimConceptLinkResult,
        RelationshipType,
        LinkingError,
        ConceptCandidate,
        AgentClassificationResult,
    )
    from .neo4j_operations import ClaimConceptNeo4jManager
    from .markdown_updater import Tier2MarkdownUpdater

    __all__ = [
        "ClaimConceptLinker",
        "ClaimConceptLinkerAgent",
        "ClaimConceptPair",
        "ClaimConceptLinkResult",
        "RelationshipType",
        "LinkingError",
        "ConceptCandidate",
        "AgentClassificationResult",
        "ClaimConceptNeo4jManager",
        "Tier2MarkdownUpdater",
    ]
except ImportError:
    # If some modules don't exist (e.g., during partial implementation),
    # only export the main orchestrator
    __all__ = ["ClaimConceptLinker"]

"""
Claim-Concept Linking Module.

This module provides the orchestration logic for linking Claim nodes to Concept nodes
in the aclarai knowledge graph using LLM-based classification.
"""

from .orchestrator import ClaimConceptLinker

__all__ = ["ClaimConceptLinker"]

"""
Core Claimify pipeline components.

This module implements the three main stages of the Claimify pipeline:
- Selection: Identifies sentence chunks that contain verifiable information
- Disambiguation: Rewrites sentences to remove ambiguities and add context
- Decomposition: Breaks sentences into atomic, self-contained claims

The pipeline follows the architecture described in docs/arch/on-claim_generation.md
and supports model injection and context windowing as per design_config_panel.md.
"""

from .data_models import (
    SentenceChunk,
    ClaimifyContext,
    SelectionResult,
    DisambiguationResult,
    DecompositionResult,
    ClaimifyResult,
    ClaimifyConfig,
)
from .pipeline import ClaimifyPipeline
from .agents import SelectionAgent, DisambiguationAgent, DecompositionAgent

__all__ = [
    "SentenceChunk",
    "ClaimifyContext", 
    "SelectionResult",
    "DisambiguationResult",
    "DecompositionResult",
    "ClaimifyResult",
    "ClaimifyConfig",
    "ClaimifyPipeline",
    "SelectionAgent",
    "DisambiguationAgent", 
    "DecompositionAgent",
]
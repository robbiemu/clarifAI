"""
Core Claimify pipeline components.
This module implements the three main stages of the Claimify pipeline:
- Selection: Identifies sentence chunks that contain verifiable information
- Disambiguation: Rewrites sentences to remove ambiguities and add context
- Decomposition: Breaks sentences into atomic, self-contained claims
The pipeline follows the architecture described in docs/arch/on-claim_generation.md
and supports model injection and context windowing as per design_config_panel.md.
"""

from .agents import DecompositionAgent, DisambiguationAgent, SelectionAgent
from .config_integration import (
    get_model_config_for_stage,
    load_claimify_config_from_file,
    load_claimify_config_from_yaml,
)
from .data_models import (
    ClaimifyConfig,
    ClaimifyContext,
    ClaimifyResult,
    DecompositionResult,
    DisambiguationResult,
    NodeType,
    SelectionResult,
    SentenceChunk,
)
from .integration import ClaimifyGraphIntegration, create_graph_manager_from_config
from .pipeline import ClaimifyPipeline

__all__ = [
    "SentenceChunk",
    "ClaimifyContext",
    "SelectionResult",
    "DisambiguationResult",
    "DecompositionResult",
    "ClaimifyResult",
    "ClaimifyConfig",
    "NodeType",
    "ClaimifyPipeline",
    "SelectionAgent",
    "DisambiguationAgent",
    "DecompositionAgent",
    "load_claimify_config_from_yaml",
    "load_claimify_config_from_file",
    "get_model_config_for_stage",
    "ClaimifyGraphIntegration",
    "create_graph_manager_from_config",
]

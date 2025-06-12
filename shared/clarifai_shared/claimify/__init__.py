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
    NodeType,
)
from .pipeline import ClaimifyPipeline
from .agents import SelectionAgent, DisambiguationAgent, DecompositionAgent
from .config_integration import (
    load_claimify_config_from_yaml,
    load_claimify_config_from_file,
    get_model_config_for_stage,
)

# Only import integration if Neo4j is available
try:
    from .integration import ClaimifyGraphIntegration, create_graph_manager_from_config
    NEO4J_INTEGRATION_AVAILABLE = True
except ImportError:
    NEO4J_INTEGRATION_AVAILABLE = False
    ClaimifyGraphIntegration = None
    create_graph_manager_from_config = None

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
]

# Add integration classes if available
if NEO4J_INTEGRATION_AVAILABLE:
    __all__.extend([
        "ClaimifyGraphIntegration",
        "create_graph_manager_from_config",
    ])

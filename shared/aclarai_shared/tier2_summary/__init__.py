"""
Tier 2 Summary Agent module.
This module implements the Tier 2 Summary Agent that aggregates and summarizes
selected Tier 1 blocks into semantically coherent groupings, as specified in
docs/arch/on-writing_vault_documents.md.
"""

from .agent import Tier2SummaryAgent
from .data_models import SummaryBlock, SummaryInput, SummaryResult, generate_summary_id

__all__ = [
    "Tier2SummaryAgent",
    "SummaryInput",
    "SummaryBlock",
    "SummaryResult",
    "generate_summary_id",
]

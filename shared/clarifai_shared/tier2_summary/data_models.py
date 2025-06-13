"""
Data models for the Tier 2 Summary Agent.

Defines the core data structures used for summary generation from grouped
Claims and Sentences, following the architecture in on-writing_vault_documents.md.
"""

import logging
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import uuid

logger = logging.getLogger(__name__)


@dataclass
class SummaryInput:
    """
    Input data representing a grouped set of Claims and/or Sentences to summarize.
    
    This represents a semantically coherent cluster of content identified by
    vector search as described in the Tier 2 retrieval notes.
    """
    
    claims: List[Dict[str, Any]] = field(default_factory=list)  # Claim nodes from Neo4j
    sentences: List[Dict[str, Any]] = field(default_factory=list)  # Sentence nodes from Neo4j
    group_context: Optional[str] = None  # Optional thematic context for the group
    
    @property
    def all_texts(self) -> List[str]:
        """Get all text content from claims and sentences."""
        texts = []
        for claim in self.claims:
            texts.append(claim.get('text', ''))
        for sentence in self.sentences:
            texts.append(sentence.get('text', ''))
        return [text for text in texts if text.strip()]
    
    @property
    def source_block_ids(self) -> List[str]:
        """Get all unique source block IDs from claims and sentences."""
        block_ids = set()
        for claim in self.claims:
            if 'block_id' in claim:
                block_ids.add(claim['block_id'])
        for sentence in self.sentences:
            if 'block_id' in sentence:
                block_ids.add(sentence['block_id'])
        return list(block_ids)


@dataclass
class SummaryBlock:
    """
    Represents a single summary block to be written to Tier 2 Markdown.
    
    Follows the structure specified in on-writing_vault_documents.md:
    - <summary sentence> ^clm_<id>
    - ...
    
    <!-- clarifai:id=clm_<id> ver=N -->
    ^clm_<id>
    """
    
    summary_text: str
    clarifai_id: str
    version: int = 1
    source_block_ids: List[str] = field(default_factory=list)  # Links back to Tier 1
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        """Set timestamp if not provided."""
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)
    
    def to_markdown(self) -> str:
        """
        Convert to Markdown format following the Tier 2 structure.
        
        Returns:
            Markdown string with summary content and metadata
        """
        lines = []
        
        # Summary content as bullet points
        summary_lines = self.summary_text.strip().split('\n')
        for line in summary_lines:
            line = line.strip()
            if line:
                if not line.startswith('- '):
                    line = f"- {line}"
                lines.append(line)
        
        # Add the summary ID anchor to the last line
        if lines:
            lines[-1] = f"{lines[-1]} ^{self.clarifai_id}"
        
        lines.append("")  # Empty line before metadata
        
        # Add metadata comment
        lines.append(f"<!-- clarifai:id={self.clarifai_id} ver={self.version} -->")
        lines.append(f"^{self.clarifai_id}")
        
        return "\n".join(lines)


@dataclass
class SummaryResult:
    """
    Result of Tier 2 summary generation for a file.
    
    Contains all summary blocks that should be written to the Tier 2 file,
    along with metadata about the processing.
    """
    
    summary_blocks: List[SummaryBlock] = field(default_factory=list)
    source_file_context: Optional[str] = None  # Original conversation context
    processing_time: Optional[float] = None
    model_used: Optional[str] = None
    error: Optional[str] = None
    
    def to_markdown(self, title: Optional[str] = None) -> str:
        """
        Convert all summary blocks to a complete Tier 2 Markdown file.
        
        Args:
            title: Optional title for the file
            
        Returns:
            Complete Markdown content for the Tier 2 file
        """
        lines = []
        
        # Add title if provided
        if title:
            lines.append(f"# {title}")
            lines.append("")
        
        # Add file-level metadata if available
        if self.source_file_context:
            lines.append(f"<!-- clarifai:source_context={self.source_file_context} -->")
            lines.append("")
        
        # Add each summary block
        for i, block in enumerate(self.summary_blocks):
            if i > 0:
                lines.append("")  # Empty line between blocks
            lines.append(block.to_markdown())
        
        return "\n".join(lines)
    
    @property
    def is_successful(self) -> bool:
        """Check if the summary generation was successful."""
        return self.error is None and len(self.summary_blocks) > 0


def generate_summary_id() -> str:
    """Generate a unique ID for a summary block following the clm_ pattern."""
    return f"clm_{uuid.uuid4().hex[:8]}"
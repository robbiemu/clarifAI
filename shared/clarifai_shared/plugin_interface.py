"""
Base plugin interface and data structures for ClarifAI format conversion.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, List, Optional


@dataclass
class MarkdownOutput:
    """Structure for plugin output containing Markdown content and metadata."""
    
    title: str                 # Will be overwritten if missing
    markdown_text: str        # Full Markdown content to write
    metadata: Optional[Dict[str, Any]] = None  # Optional fields described in docs


class Plugin(ABC):
    """Abstract base class for all format conversion plugins."""
    
    @abstractmethod
    def can_accept(self, raw_input: str) -> bool:
        """
        Determine if this plugin can handle the given input.
        
        Args:
            raw_input: The raw text content of the file
            
        Returns:
            True if this plugin can process the input, False otherwise
        """
        pass

    @abstractmethod
    def convert(self, raw_input: str, path: Path) -> List[MarkdownOutput]:
        """
        Convert the raw input to one or more MarkdownOutput objects.
        
        Args:
            raw_input: The raw text content of the file
            path: Path to the input file
            
        Returns:
            List of MarkdownOutput objects representing conversations
        """
        pass


class UnknownFormatError(Exception):
    """Raised when no plugin can handle a given input format."""
    pass
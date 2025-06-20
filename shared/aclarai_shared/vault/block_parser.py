"""
Shared block parser utilities for aclarai vault synchronization.
This module provides common functionality for parsing Markdown files to extract
aclarai:id blocks and their semantic content. It's used by both the periodic
VaultSyncJob and the reactive DirtyBlockConsumer to ensure consistent parsing.
"""

import hashlib
import re
from typing import Any, Dict, List


class BlockParser:
    """
    Shared utilities for parsing aclarai:id blocks from Markdown content.
    This class provides the common block parsing logic used by both:
    - VaultSyncJob (periodic synchronization)
    - DirtyBlockConsumer (reactive synchronization)
    """

    def __init__(self):
        """Initialize the block parser."""
        pass

    def extract_aclarai_blocks(self, content: str) -> List[Dict[str, Any]]:
        """
        Extract blocks with aclarai:id from Markdown content.
        Handles both inline blocks and file-level blocks following
        docs/arch/on-graph_vault_synchronization.md patterns.
        Args:
            content: The Markdown content as a string
        Returns:
            List of block dictionaries with aclarai_id, version, semantic_text,
            content_hash, and comment_position
        """
        blocks = []
        # Pattern for aclarai:id comments
        # Supports both formats: "<!-- aclarai:id=xxx ver=N -->" and "<!-- aclarai:id=xxx -->"
        id_pattern = r"<!--\s*aclarai:id=([^-\s]+)(?:\s+ver=(\d+))?\s*-->"
        # Find all aclarai:id comments
        for match in re.finditer(id_pattern, content):
            aclarai_id = match.group(1)
            version = int(match.group(2)) if match.group(2) else 1
            comment_pos = match.start()
            # Extract semantic text for this block
            semantic_text = self.extract_semantic_text_for_block(content, match)
            # Skip blocks with no content (shouldn't happen but defensive)
            if not semantic_text:
                continue
            # Calculate hash of semantic text
            content_hash = self.calculate_content_hash(semantic_text)
            block = {
                "aclarai_id": aclarai_id,
                "version": version,
                "semantic_text": semantic_text,
                "content_hash": content_hash,
                "comment_position": comment_pos,
            }
            blocks.append(block)
        return blocks

    def extract_semantic_text_for_block(self, content: str, id_match: re.Match) -> str:
        """
        Extract the semantic text (visible content) for a aclarai:id block.
        This implements the semantic_text concept by extracting the visible text
        while excluding metadata comments.
        Args:
            content: Full Markdown content
            id_match: Regex match object for the aclarai:id comment
        Returns:
            The semantic text for this block
        """
        comment_pos = id_match.start()
        # Check if this is a file-level block (comment near end of file)
        remaining_content = content[comment_pos:].strip()
        if (
            len(remaining_content) <= len(id_match.group(0)) + 10
        ):  # Small buffer for whitespace
            # File-level block - hash entire file content excluding the comment
            semantic_text = content[:comment_pos].strip()
        else:
            # Inline block - find the text before the comment
            # Look backwards to find the start of the block
            lines_before_comment = content[:comment_pos].split("\n")
            # For inline blocks, typically the semantic text is the content on the same line
            # or the paragraph/block that precedes the comment
            if lines_before_comment:
                # Take the last non-empty line before the comment as the semantic text
                semantic_text = lines_before_comment[-1].strip()
                # If the comment is on its own line, look for preceding content
                if not semantic_text:
                    # Find the last non-empty line
                    for line in reversed(lines_before_comment[:-1]):
                        if line.strip():
                            semantic_text = line.strip()
                            break
            else:
                semantic_text = ""
        return semantic_text

    def calculate_content_hash(self, semantic_text: str) -> str:
        """
        Calculate SHA-256 hash of semantic text content.
        Args:
            semantic_text: The semantic text to hash
        Returns:
            Hexadecimal string representation of the hash
        """
        # Normalize whitespace and encoding for consistent hashing
        normalized_text = " ".join(semantic_text.split())
        return hashlib.sha256(normalized_text.encode("utf-8")).hexdigest()

    def find_block_by_id(self, content: str, aclarai_id: str) -> Dict[str, Any] | None:
        """
        Find a specific block by aclarai_id in the content.
        Args:
            content: The Markdown content as a string
            aclarai_id: The aclarai:id to search for
        Returns:
            Block dictionary if found, None otherwise
        """
        blocks = self.extract_aclarai_blocks(content)
        for block in blocks:
            if block["aclarai_id"] == aclarai_id:
                return block
        return None

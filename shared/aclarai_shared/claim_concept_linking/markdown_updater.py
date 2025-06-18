"""
Markdown updater for Tier 2 files with concept wikilinks.

This module handles updating Tier 2 Markdown files to include [[wikilinks]]
for linked concepts, following the atomic write patterns from
docs/arch/on-filehandle_conflicts.md.
"""

import logging
import re
from pathlib import Path
from typing import List, Optional, Dict, Any

from ..config import aclaraiConfig, load_config
from ..import_system import write_file_atomically
from .models import ClaimConceptLinkResult

logger = logging.getLogger(__name__)


class Tier2MarkdownUpdater:
    """
    Updates Tier 2 Markdown files with concept wikilinks.

    This class handles finding Tier 2 files that contain linked claims
    and adding [[concept]] wikilinks while preserving aclarai:id anchors
    and incrementing version numbers.
    """

    def __init__(self, config: Optional[aclaraiConfig] = None):
        """
        Initialize the Tier 2 Markdown updater.

        Args:
            config: aclarai configuration (loads default if None)
        """
        self.config = config or load_config()

        # Get vault and Tier 2 directory paths
        self.vault_path = Path(self.config.vault_path)

        # Tier 2 summaries are typically in the root or a summaries subdirectory
        tier2_path = getattr(self.config.paths, "tier2", None) or ""
        if tier2_path:
            self.tier2_dir = self.vault_path / tier2_path
        else:
            self.tier2_dir = self.vault_path  # Default to vault root

        logger.info(
            f"Initialized Tier2MarkdownUpdater for directory: {self.tier2_dir}",
            extra={
                "service": "aclarai",
                "filename.function_name": "claim_concept_linking.Tier2MarkdownUpdater.__init__",
                "tier2_dir": str(self.tier2_dir),
            },
        )

    def update_files_with_links(
        self, link_results: List[ClaimConceptLinkResult]
    ) -> Dict[str, Any]:
        """
        Update Tier 2 Markdown files with concept wikilinks.

        Args:
            link_results: List of successful claim-concept links

        Returns:
            Dictionary with update statistics
        """
        stats = {
            "files_processed": 0,
            "files_updated": 0,
            "links_added": 0,
            "errors": [],
        }

        # Group links by aclarai_id to process files efficiently
        links_by_file = self._group_links_by_file(link_results)

        for aclarai_id, file_links in links_by_file.items():
            try:
                updated = self._update_single_file(aclarai_id, file_links)
                stats["files_processed"] += 1

                if updated:
                    stats["files_updated"] += 1
                    stats["links_added"] += len(file_links)

            except Exception as e:
                error_msg = f"Failed to update file for {aclarai_id}: {e}"
                stats["errors"].append(error_msg)
                logger.error(
                    error_msg,
                    extra={
                        "service": "aclarai",
                        "filename.function_name": "claim_concept_linking.Tier2MarkdownUpdater.update_files_with_links",
                        "aclarai_id": aclarai_id,
                        "error": str(e),
                    },
                )

        logger.info(
            "Completed Tier 2 file updates",
            extra={
                "service": "aclarai",
                "filename.function_name": "claim_concept_linking.Tier2MarkdownUpdater.update_files_with_links",
                **stats,
            },
        )

        return stats

    def _group_links_by_file(
        self, link_results: List[ClaimConceptLinkResult]
    ) -> Dict[str, List[ClaimConceptLinkResult]]:
        """
        Group link results by the aclarai_id of their source file.

        Note: This is a placeholder implementation. In practice, we would
        need to query Neo4j to find which file contains each claim.

        Args:
            link_results: List of link results

        Returns:
            Dictionary mapping aclarai_id to list of links for that file
        """
        # TODO: Implement actual file lookup via Neo4j
        # For now, return empty dict to avoid errors during testing
        logger.warning(
            "File lookup not implemented - would need Neo4j query to map claims to files",
            extra={
                "service": "aclarai",
                "filename.function_name": "claim_concept_linking.Tier2MarkdownUpdater._group_links_by_file",
                "link_count": len(link_results),
            },
        )
        return {}

    def _update_single_file(
        self, aclarai_id: str, file_links: List[ClaimConceptLinkResult]
    ) -> bool:
        """
        Update a single Tier 2 file with concept wikilinks.

        Args:
            aclarai_id: The aclarai_id of the file to update
            file_links: List of links to add to this file

        Returns:
            True if file was updated, False otherwise
        """
        # Find the file containing this aclarai_id
        file_path = self._find_file_by_aclarai_id(aclarai_id)
        if not file_path:
            logger.warning(
                f"Could not find file for aclarai_id: {aclarai_id}",
                extra={
                    "service": "aclarai",
                    "filename.function_name": "claim_concept_linking.Tier2MarkdownUpdater._update_single_file",
                    "aclarai_id": aclarai_id,
                },
            )
            return False

        try:
            # Read the current file content
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Update content with wikilinks
            updated_content = self._add_wikilinks_to_content(content, file_links)

            # Only write if content changed
            if updated_content != content:
                # Increment version in the content
                updated_content = self._increment_version(updated_content)

                # Write atomically
                write_file_atomically(file_path, updated_content)

                logger.info(
                    f"Updated file with concept wikilinks: {file_path.name}",
                    extra={
                        "service": "aclarai",
                        "filename.function_name": "claim_concept_linking.Tier2MarkdownUpdater._update_single_file",
                        "file_path": str(file_path),
                        "aclarai_id": aclarai_id,
                        "links_added": len(file_links),
                    },
                )
                return True

            return False

        except Exception as e:
            logger.error(
                f"Failed to update file {file_path}: {e}",
                extra={
                    "service": "aclarai",
                    "filename.function_name": "claim_concept_linking.Tier2MarkdownUpdater._update_single_file",
                    "file_path": str(file_path),
                    "aclarai_id": aclarai_id,
                    "error": str(e),
                },
            )
            raise

    def _find_file_by_aclarai_id(self, aclarai_id: str) -> Optional[Path]:
        """
        Find the Tier 2 file containing the given aclarai_id.

        Args:
            aclarai_id: The aclarai_id to search for

        Returns:
            Path to the file if found, None otherwise
        """
        # Search for Markdown files in the Tier 2 directory
        for file_path in self.tier2_dir.rglob("*.md"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Look for the aclarai_id in the content
                if f"aclarai:id={aclarai_id}" in content:
                    return file_path

            except Exception as e:
                logger.debug(
                    f"Error reading file {file_path}: {e}",
                    extra={
                        "service": "aclarai",
                        "filename.function_name": "claim_concept_linking.Tier2MarkdownUpdater._find_file_by_aclarai_id",
                        "file_path": str(file_path),
                        "error": str(e),
                    },
                )

        return None

    def _add_wikilinks_to_content(
        self, content: str, file_links: List[ClaimConceptLinkResult]
    ) -> str:
        """
        Add concept wikilinks to the content.

        This method finds text passages that match linked claims and adds
        [[concept]] wikilinks for the concepts they reference.

        Args:
            content: The original file content
            file_links: List of links for this file

        Returns:
            Updated content with wikilinks added
        """
        updated_content = content

        # Extract unique concepts to link
        concepts_to_link = {link.concept_id for link in file_links}

        # For each concept, add a wikilink
        # This is a simple implementation - in practice we'd want more
        # sophisticated text matching and placement
        for concept_id in concepts_to_link:
            # Find the concept text from one of the links
            concept_text = None
            for link in file_links:
                if link.concept_id == concept_id:
                    # We'd need to get the concept text from Neo4j
                    # For now, use the concept_id as placeholder
                    concept_text = concept_id
                    break

            if concept_text:
                # Add wikilink at the end of relevant sections
                # This is a placeholder implementation
                wikilink = f"[[{concept_text}]]"

                # Only add if not already present
                if wikilink not in updated_content:
                    # Find a good place to insert the link
                    # For now, add to the end of the content before the anchor
                    anchor_pattern = r"(\^[a-zA-Z0-9_]+\s*$)"
                    if re.search(anchor_pattern, updated_content, re.MULTILINE):
                        updated_content = re.sub(
                            anchor_pattern,
                            f"\n\nSee also: {wikilink}\n\n\\1",
                            updated_content,
                            count=1,
                            flags=re.MULTILINE,
                        )
                    else:
                        updated_content += f"\n\nSee also: {wikilink}"

        return updated_content

    def _increment_version(self, content: str) -> str:
        """
        Increment the version number in the aclarai metadata.

        Args:
            content: The file content

        Returns:
            Content with incremented version
        """
        # Pattern to match aclarai:id=... ver=N
        version_pattern = r"(aclarai:id=[^\s]+)\s+ver=(\d+)"

        def increment_match(match):
            aclarai_part = match.group(1)
            current_version = int(match.group(2))
            new_version = current_version + 1
            return f"{aclarai_part} ver={new_version}"

        updated_content = re.sub(version_pattern, increment_match, content)

        return updated_content

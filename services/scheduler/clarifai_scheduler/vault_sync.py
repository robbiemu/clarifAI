"""
Vault synchronization utilities for ClarifAI scheduler.

This module implements the vault-to-graph sync job that maintains consistency
between Markdown files and the Neo4j knowledge graph by detecting changes
through content hashing and updating graph nodes accordingly.
"""

import hashlib
import logging
import re
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

from clarifai_shared import load_config
from clarifai_shared.graph.neo4j_manager import Neo4jGraphManager


logger = logging.getLogger(__name__)


class VaultSyncJob:
    """
    Job for synchronizing vault Markdown files with Neo4j graph.
    
    Follows the block-level synchronization strategy from 
    docs/arch/on-graph_vault_synchronization.md.
    """

    def __init__(self, config=None):
        """Initialize vault sync job."""
        self.config = config or load_config(validate=True)
        self.graph_manager = Neo4jGraphManager(self.config)
        
        # Vault paths from config
        self.vault_path = Path(self.config.vault_path)
        self.tier1_path = self.vault_path / self.config.paths.tier1
        self.tier2_path = self.vault_path / self.config.paths.tier2
        self.tier3_path = self.vault_path / self.config.paths.tier3

    def run_sync(self) -> Dict[str, Any]:
        """
        Run the complete vault synchronization job.
        
        Returns:
            Dictionary with sync statistics and results
        """
        start_time = time.time()
        
        logger.info(
            "vault_sync.run_sync: Starting vault synchronization job",
            extra={
                "service": "clarifai-scheduler",
                "filename.function_name": "vault_sync.run_sync",
                "job_id": f"vault_sync_{int(start_time)}",
            }
        )
        
        try:
            # Statistics tracking
            stats = {
                "files_processed": 0,
                "blocks_processed": 0,
                "blocks_unchanged": 0,
                "blocks_updated": 0,
                "blocks_new": 0,
                "errors": 0,
                "start_time": start_time,
                "end_time": None,
                "duration": None
            }
            
            # Process Tier 1 files (required)
            logger.info(
                "vault_sync.run_sync: Processing Tier 1 files",
                extra={
                    "service": "clarifai-scheduler", 
                    "filename.function_name": "vault_sync.run_sync",
                    "tier": "tier1",
                    "path": str(self.tier1_path)
                }
            )
            tier1_stats = self._process_tier_files(self.tier1_path, "tier1")
            self._merge_stats(stats, tier1_stats)
            
            # Process other tiers if they contain clarifai:id blocks
            for tier_name, tier_path in [("tier2", self.tier2_path), ("tier3", self.tier3_path)]:
                if tier_path.exists():
                    logger.info(
                        f"vault_sync.run_sync: Processing {tier_name} files",
                        extra={
                            "service": "clarifai-scheduler",
                            "filename.function_name": "vault_sync.run_sync", 
                            "tier": tier_name,
                            "path": str(tier_path)
                        }
                    )
                    tier_stats = self._process_tier_files(tier_path, tier_name)
                    self._merge_stats(stats, tier_stats)
            
            # Finalize stats
            end_time = time.time()
            stats["end_time"] = end_time
            stats["duration"] = end_time - start_time
            
            logger.info(
                "vault_sync.run_sync: Vault synchronization completed successfully",
                extra={
                    "service": "clarifai-scheduler",
                    "filename.function_name": "vault_sync.run_sync",
                    "files_processed": stats["files_processed"],
                    "blocks_processed": stats["blocks_processed"],
                    "blocks_updated": stats["blocks_updated"],
                    "blocks_new": stats["blocks_new"],
                    "duration": stats["duration"],
                    "errors": stats["errors"]
                }
            )
            
            return stats
            
        except Exception as e:
            logger.error(
                f"vault_sync.run_sync: Vault synchronization failed: {e}",
                extra={
                    "service": "clarifai-scheduler",
                    "filename.function_name": "vault_sync.run_sync",
                    "error": str(e)
                }
            )
            raise

    def _process_tier_files(self, tier_path: Path, tier_name: str) -> Dict[str, int]:
        """Process all Markdown files in a tier directory."""
        stats = {
            "files_processed": 0,
            "blocks_processed": 0,
            "blocks_unchanged": 0,
            "blocks_updated": 0,
            "blocks_new": 0,
            "errors": 0
        }
        
        if not tier_path.exists():
            logger.warning(
                f"vault_sync._process_tier_files: Tier path does not exist: {tier_path}",
                extra={
                    "service": "clarifai-scheduler",
                    "filename.function_name": "vault_sync._process_tier_files",
                    "tier": tier_name,
                    "path": str(tier_path)
                }
            )
            return stats
            
        # Find all markdown files
        md_files = list(tier_path.glob("**/*.md"))
        
        logger.info(
            f"vault_sync._process_tier_files: Found {len(md_files)} markdown files in {tier_name}",
            extra={
                "service": "clarifai-scheduler",
                "filename.function_name": "vault_sync._process_tier_files",
                "tier": tier_name,
                "file_count": len(md_files)
            }
        )
        
        for md_file in md_files:
            try:
                file_stats = self._process_markdown_file(md_file, tier_name)
                self._merge_stats(stats, file_stats)
                stats["files_processed"] += 1
                
            except Exception as e:
                logger.error(
                    f"vault_sync._process_tier_files: Error processing file {md_file}: {e}",
                    extra={
                        "service": "clarifai-scheduler",
                        "filename.function_name": "vault_sync._process_tier_files",
                        "tier": tier_name,
                        "file": str(md_file),
                        "error": str(e)
                    }
                )
                stats["errors"] += 1
                
        return stats

    def _process_markdown_file(self, file_path: Path, tier_name: str) -> Dict[str, int]:
        """Process a single Markdown file for clarifai:id blocks."""
        stats = {
            "blocks_processed": 0,
            "blocks_unchanged": 0,
            "blocks_updated": 0,
            "blocks_new": 0,
            "errors": 0
        }
        
        try:
            # Read file content
            content = file_path.read_text(encoding='utf-8')
            
            # Extract clarifai:id blocks
            blocks = self._extract_clarifai_blocks(content)
            
            if not blocks:
                logger.debug(
                    f"vault_sync._process_markdown_file: No clarifai:id blocks found in {file_path}",
                    extra={
                        "service": "clarifai-scheduler",
                        "filename.function_name": "vault_sync._process_markdown_file",
                        "file": str(file_path),
                        "tier": tier_name
                    }
                )
                return stats
            
            logger.debug(
                f"vault_sync._process_markdown_file: Found {len(blocks)} clarifai:id blocks in {file_path}",
                extra={
                    "service": "clarifai-scheduler",
                    "filename.function_name": "vault_sync._process_markdown_file",
                    "file": str(file_path),
                    "tier": tier_name,
                    "block_count": len(blocks)
                }
            )
            
            # Process each block
            for block in blocks:
                try:
                    block_stats = self._sync_block_with_graph(block, file_path)
                    self._merge_stats(stats, block_stats)
                    stats["blocks_processed"] += 1
                    
                except Exception as e:
                    logger.error(
                        f"vault_sync._process_markdown_file: Error processing block {block.get('clarifai_id', 'unknown')}: {e}",
                        extra={
                            "service": "clarifai-scheduler",
                            "filename.function_name": "vault_sync._process_markdown_file",
                            "file": str(file_path),
                            "clarifai_id": block.get('clarifai_id', 'unknown'),
                            "error": str(e)
                        }
                    )
                    stats["errors"] += 1
                    
        except Exception as e:
            logger.error(
                f"vault_sync._process_markdown_file: Error reading file {file_path}: {e}",
                extra={
                    "service": "clarifai-scheduler",
                    "filename.function_name": "vault_sync._process_markdown_file",
                    "file": str(file_path),
                    "error": str(e)
                }
            )
            stats["errors"] += 1
            
        return stats

    def _extract_clarifai_blocks(self, content: str) -> List[Dict[str, Any]]:
        """
        Extract blocks with clarifai:id from Markdown content.
        
        Handles both inline blocks and file-level blocks following
        docs/arch/on-graph_vault_synchronization.md patterns.
        """
        blocks = []
        
        # Pattern for clarifai:id comments with optional version
        # Matches: <!-- clarifai:id=xxx ver=N --> or <!-- clarifai:id=xxx -->
        id_pattern = r'<!--\s*clarifai:id=([^-\s]+)(?:\s+ver=(\d+))?\s*-->'
        
        # Find all clarifai:id comments
        for match in re.finditer(id_pattern, content):
            clarifai_id = match.group(1)
            version = int(match.group(2)) if match.group(2) else 1
            comment_pos = match.start()
            
            # Extract semantic text for this block
            semantic_text = self._extract_semantic_text_for_block(content, match)
            
            # Calculate hash of semantic text
            content_hash = self._calculate_content_hash(semantic_text)
            
            block = {
                "clarifai_id": clarifai_id,
                "version": version,
                "semantic_text": semantic_text,
                "content_hash": content_hash,
                "comment_position": comment_pos
            }
            
            blocks.append(block)
            
        return blocks

    def _extract_semantic_text_for_block(self, content: str, id_match: re.Match) -> str:
        """
        Extract the semantic text (visible content) for a clarifai:id block.
        
        This implements the semantic_text concept from on-refreshing_concept_embeddings.md
        by extracting the visible text while excluding metadata comments.
        """
        comment_pos = id_match.start()
        
        # Check if this is a file-level block (comment near end of file)
        remaining_content = content[comment_pos:].strip()
        if len(remaining_content) <= len(id_match.group(0)) + 10:  # Small buffer for whitespace
            # File-level block - hash entire file content excluding the comment
            semantic_text = content[:comment_pos].strip()
        else:
            # Inline block - find the text before the comment
            # Look backwards to find the start of the block
            lines_before_comment = content[:comment_pos].split('\n')
            
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

    def _calculate_content_hash(self, semantic_text: str) -> str:
        """Calculate SHA-256 hash of semantic text content."""
        # Normalize whitespace and encoding for consistent hashing
        normalized_text = ' '.join(semantic_text.split())
        return hashlib.sha256(normalized_text.encode('utf-8')).hexdigest()

    def _sync_block_with_graph(self, block: Dict[str, Any], file_path: Path) -> Dict[str, int]:
        """
        Synchronize a single block with the Neo4j graph.
        
        Returns stats about the sync operation.
        """
        stats = {
            "blocks_unchanged": 0,
            "blocks_updated": 0,
            "blocks_new": 0,
            "errors": 0
        }
        
        clarifai_id = block["clarifai_id"]
        
        try:
            # Get existing block from graph
            existing_block = self._get_block_from_graph(clarifai_id)
            
            if existing_block is None:
                # New block - create in graph
                self._create_block_in_graph(block, file_path)
                stats["blocks_new"] += 1
                
                logger.info(
                    f"vault_sync._sync_block_with_graph: Created new block in graph",
                    extra={
                        "service": "clarifai-scheduler",
                        "filename.function_name": "vault_sync._sync_block_with_graph",
                        "clarifai_id": clarifai_id,
                        "file": str(file_path),
                        "action": "create"
                    }
                )
                
            else:
                # Existing block - check if content changed
                existing_hash = existing_block.get("hash", "")
                new_hash = block["content_hash"]
                
                if existing_hash != new_hash:
                    # Content changed - update block
                    self._update_block_in_graph(block, existing_block, file_path)
                    stats["blocks_updated"] += 1
                    
                    logger.info(
                        f"vault_sync._sync_block_with_graph: Updated changed block in graph",
                        extra={
                            "service": "clarifai-scheduler",
                            "filename.function_name": "vault_sync._sync_block_with_graph",
                            "clarifai_id": clarifai_id,
                            "file": str(file_path),
                            "action": "update",
                            "old_hash": existing_hash[:8],  # Log first 8 chars for brevity
                            "new_hash": new_hash[:8]
                        }
                    )
                else:
                    # No change
                    stats["blocks_unchanged"] += 1
                    
                    logger.debug(
                        f"vault_sync._sync_block_with_graph: Block unchanged",
                        extra={
                            "service": "clarifai-scheduler",
                            "filename.function_name": "vault_sync._sync_block_with_graph",
                            "clarifai_id": clarifai_id,
                            "action": "unchanged"
                        }
                    )
                    
        except Exception as e:
            logger.error(
                f"vault_sync._sync_block_with_graph: Error syncing block {clarifai_id}: {e}",
                extra={
                    "service": "clarifai-scheduler",
                    "filename.function_name": "vault_sync._sync_block_with_graph",
                    "clarifai_id": clarifai_id,
                    "file": str(file_path),
                    "error": str(e)
                }
            )
            stats["errors"] += 1
            
        return stats

    def _get_block_from_graph(self, clarifai_id: str) -> Optional[Dict[str, Any]]:
        """Get block properties from Neo4j graph by clarifai_id."""
        cypher_query = """
        MATCH (b:Block {id: $clarifai_id})
        RETURN b.id as id, b.text as text, b.hash as hash, 
               b.version as version, b.last_updated as last_updated,
               b.needs_reprocessing as needs_reprocessing
        """
        
        def _execute_get_block():
            with self.graph_manager.session() as session:
                result = session.run(cypher_query, clarifai_id=clarifai_id)
                record = result.single()
                return dict(record) if record else None
                
        return self.graph_manager._retry_with_backoff(_execute_get_block)

    def _create_block_in_graph(self, block: Dict[str, Any], file_path: Path):
        """Create a new block in the Neo4j graph."""
        current_time = datetime.utcnow().isoformat()
        
        cypher_query = """
        MERGE (b:Block {id: $clarifai_id})
        ON CREATE SET
            b.text = $text,
            b.hash = $hash,
            b.version = $version,
            b.last_updated = datetime($last_updated),
            b.needs_reprocessing = true,
            b.source_file = $source_file
        """
        
        def _execute_create_block():
            with self.graph_manager.session() as session:
                session.run(
                    cypher_query,
                    clarifai_id=block["clarifai_id"],
                    text=block["semantic_text"],
                    hash=block["content_hash"],
                    version=block["version"],
                    last_updated=current_time,
                    source_file=str(file_path)
                )
                
        self.graph_manager._retry_with_backoff(_execute_create_block)

    def _update_block_in_graph(self, block: Dict[str, Any], existing_block: Dict[str, Any], file_path: Path):
        """Update an existing block in the Neo4j graph."""
        current_time = datetime.utcnow().isoformat()
        new_version = block["version"]  # Use version from vault file
        
        cypher_query = """
        MATCH (b:Block {id: $clarifai_id})
        SET b.text = $text,
            b.hash = $hash,
            b.version = $version,
            b.last_updated = datetime($last_updated),
            b.needs_reprocessing = true,
            b.source_file = $source_file
        """
        
        def _execute_update_block():
            with self.graph_manager.session() as session:
                session.run(
                    cypher_query,
                    clarifai_id=block["clarifai_id"],
                    text=block["semantic_text"],
                    hash=block["content_hash"],
                    version=new_version,
                    last_updated=current_time,
                    source_file=str(file_path)
                )
                
        self.graph_manager._retry_with_backoff(_execute_update_block)

    def _merge_stats(self, target: Dict[str, int], source: Dict[str, int]):
        """Merge statistics from source into target."""
        for key in ["files_processed", "blocks_processed", "blocks_unchanged", 
                   "blocks_updated", "blocks_new", "errors"]:
            if key in source:
                target[key] += source[key]

    def close(self):
        """Clean up resources."""
        if hasattr(self, 'graph_manager'):
            self.graph_manager.close()
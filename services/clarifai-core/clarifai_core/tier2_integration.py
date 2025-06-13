"""
Tier 2 Summary Integration for ClarifAI Core Service.

This module provides the integration point for the Tier 2 Summary Agent within
the clarifai-core service, following the architectural patterns established
for service integration.
"""

import logging
from pathlib import Path
from typing import List, Optional

from clarifai_shared.config import ClarifAIConfig, load_config
from clarifai_shared.tier2_summary import Tier2SummaryAgent
from clarifai_shared.graph.neo4j_manager import Neo4jGraphManager
from clarifai_shared.embedding.storage import ClarifAIVectorStore

logger = logging.getLogger(__name__)


class Tier2SummaryService:
    """
    Service integration for Tier 2 Summary generation.
    
    Provides a high-level interface for generating Tier 2 summaries
    within the clarifai-core service context.
    """
    
    def __init__(self, config: Optional[ClarifAIConfig] = None):
        """
        Initialize the Tier 2 Summary Service.
        
        Args:
            config: ClarifAI configuration (loads default if None)
        """
        self.config = config or load_config()
        
        # Initialize the core agent
        self.agent = Tier2SummaryAgent(config=self.config)
        
        logger.info(
            "Initialized Tier2SummaryService",
            extra={
                "service": "clarifai-core",
                "filename.function_name": "tier2_integration.Tier2SummaryService.__init__",
            }
        )
    
    def generate_summaries(
        self,
        output_dir: Optional[Path] = None,
        file_prefix: str = "tier2_summary",
    ) -> List[Path]:
        """
        Generate Tier 2 summaries for available content.
        
        This is the main entry point for Tier 2 summary generation that would
        typically be called from a scheduler or API endpoint.
        
        Args:
            output_dir: Directory to write summary files (uses config if not provided)
            file_prefix: Prefix for generated filenames
            
        Returns:
            List of paths to successfully written files
        """
        logger.info(
            "Starting Tier 2 summary generation",
            extra={
                "service": "clarifai-core",
                "filename.function_name": "tier2_integration.Tier2SummaryService.generate_summaries",
                "output_dir": str(output_dir) if output_dir else "default",
                "file_prefix": file_prefix,
            }
        )
        
        try:
            # Use the agent's complete workflow
            written_files = self.agent.process_and_generate_summaries(
                output_dir=output_dir,
                file_prefix=file_prefix
            )
            
            logger.info(
                f"Completed Tier 2 summary generation - wrote {len(written_files)} files",
                extra={
                    "service": "clarifai-core",
                    "filename.function_name": "tier2_integration.Tier2SummaryService.generate_summaries",
                    "files_written": len(written_files),
                    "file_paths": [str(p) for p in written_files],
                }
            )
            
            return written_files
            
        except Exception as e:
            logger.error(
                f"Failed to generate Tier 2 summaries: {e}",
                extra={
                    "service": "clarifai-core",
                    "filename.function_name": "tier2_integration.Tier2SummaryService.generate_summaries",
                    "error": str(e),
                }
            )
            return []
    
    def get_tier2_output_directory(self) -> Path:
        """
        Get the configured Tier 2 output directory.
        
        Returns:
            Path to the Tier 2 directory
        """
        vault_path = Path(self.config.paths.vault)
        tier2_path = self.config.paths.tier2
        return vault_path / tier2_path


def run_tier2_summary_job() -> bool:
    """
    Standalone function to run Tier 2 summary generation.
    
    This function can be called from schedulers or command-line interfaces
    to generate Tier 2 summaries.
    
    Returns:
        True if successful, False otherwise
    """
    logger.info(
        "Running Tier 2 summary job",
        extra={
            "service": "clarifai-core",
            "filename.function_name": "tier2_integration.run_tier2_summary_job",
        }
    )
    
    try:
        service = Tier2SummaryService()
        written_files = service.generate_summaries()
        
        success = len(written_files) > 0
        
        logger.info(
            f"Tier 2 summary job completed - success: {success}",
            extra={
                "service": "clarifai-core",
                "filename.function_name": "tier2_integration.run_tier2_summary_job",
                "success": success,
                "files_written": len(written_files),
            }
        )
        
        return success
        
    except Exception as e:
        logger.error(
            f"Tier 2 summary job failed: {e}",
            extra={
                "service": "clarifai-core",
                "filename.function_name": "tier2_integration.run_tier2_summary_job",
                "error": str(e),
            }
        )
        return False


if __name__ == "__main__":
    # Allow running this module directly for testing
    success = run_tier2_summary_job()
    exit(0 if success else 1)
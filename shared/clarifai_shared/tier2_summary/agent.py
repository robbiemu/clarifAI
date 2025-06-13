"""
Tier 2 Summary Agent implementation.

This agent aggregates and summarizes selected Tier 1 blocks into semantically
coherent groupings, as specified in docs/arch/on-writing_vault_documents.md.
"""

import logging
import time
from pathlib import Path
from typing import List, Optional, Dict, Any, Union

from llama_index.core.llms import LLM
from llama_index.llms.openai import OpenAI

from ..config import ClarifAIConfig
from ..graph.neo4j_manager import Neo4jGraphManager  
from ..embedding.storage import ClarifAIVectorStore
from ..import_system import write_file_atomically
from .data_models import SummaryInput, SummaryBlock, SummaryResult, generate_summary_id

logger = logging.getLogger(__name__)


class Tier2SummaryAgent:
    """
    Agent for generating Tier 2 summaries from grouped Claims and Sentences.
    
    This agent:
    1. Retrieves grouped Claims/Sentences using vector similarity
    2. Generates coherent summaries using LLM
    3. Creates properly formatted Markdown with links back to Tier 1
    4. Writes files atomically to the vault
    """
    
    def __init__(
        self,
        config: Optional[ClarifAIConfig] = None,
        neo4j_manager: Optional[Neo4jGraphManager] = None,
        embedding_storage: Optional[ClarifAIVectorStore] = None,
        llm: Optional[LLM] = None,
    ):
        """
        Initialize the Tier 2 Summary Agent.
        
        Args:
            config: ClarifAI configuration
            neo4j_manager: Neo4j graph manager for retrieving claims/sentences
            embedding_storage: Vector storage for similarity search
            llm: Language model for summary generation
        """
        self.config = config or ClarifAIConfig()
        
        # Check if tier2_generation is enabled in configuration
        tier2_enabled = self.config.features.get("tier2_generation", False)
        if not tier2_enabled:
            logger.warning(
                "Tier 2 generation is disabled in configuration",
                extra={
                    "service": "clarifai",
                    "filename.function_name": "agent.__init__",
                    "tier2_generation": tier2_enabled,
                }
            )
        
        self.neo4j_manager = neo4j_manager
        self.embedding_storage = embedding_storage
        
        # Initialize LLM
        if llm is not None:
            self.llm = llm
        else:
            # Use configured model or default
            model_name = self.config.llm.models.get("default", "gpt-3.5-turbo")
            self.llm = OpenAI(
                model=model_name,
                temperature=self.config.llm.temperature,
                max_tokens=self.config.llm.max_tokens,
            )
        
        logger.info(
            "Initialized Tier2SummaryAgent",
            extra={
                "service": "clarifai",
                "filename.function_name": "agent.__init__",
                "model": str(self.llm.model) if hasattr(self.llm, 'model') else "unknown",
            }
        )
    
    def _is_enabled(self) -> bool:
        """
        Check if Tier 2 summary generation is enabled in configuration.
        
        Returns:
            True if enabled, False otherwise
        """
        return self.config.features.get("tier2_generation", False)
    
    def _retry_with_backoff(self, func, *args, **kwargs):
        """
        Execute function with retry logic and exponential backoff.
        
        Following guidelines from docs/arch/on-error-handling-and-resilience.md
        for handling transient errors from LLM APIs and Neo4j.
        """
        max_attempts = (
            getattr(self.config, "processing", {})
            .get("retries", {})
            .get("max_attempts", 3)
        )
        backoff_factor = (
            getattr(self.config, "processing", {})
            .get("retries", {})
            .get("backoff_factor", 2)
        )
        max_wait_time = (
            getattr(self.config, "processing", {})
            .get("retries", {})
            .get("max_wait_time", 60)
        )
        
        for attempt in range(max_attempts):
            try:
                logger.debug(
                    "Retrying operation",
                    extra={
                        "service": "clarifai",
                        "filename.function_name": f"agent.{func.__name__}",
                        "attempt": attempt + 1,
                        "max_attempts": max_attempts,
                    }
                )
                return func(*args, **kwargs)
            except Exception as e:
                # Check if it's a transient error that should be retried
                is_transient = self._is_transient_error(e)
                
                if attempt == max_attempts - 1 or not is_transient:
                    error_msg = (
                        "Operation failed after retries" 
                        if is_transient 
                        else "Non-transient error occurred"
                    )
                    logger.error(
                        error_msg,
                        extra={
                            "service": "clarifai",
                            "filename.function_name": f"agent.{func.__name__}",
                            "attempt": attempt + 1,
                            "error": str(e),
                            "is_transient": is_transient,
                        }
                    )
                    raise
                
                wait_time = min(backoff_factor ** attempt, max_wait_time)
                logger.warning(
                    "Transient error occurred, retrying",
                    extra={
                        "service": "clarifai",
                        "filename.function_name": f"agent.{func.__name__}",
                        "attempt": attempt + 1,
                        "wait_time": wait_time,
                        "error": str(e),
                    }
                )
                time.sleep(wait_time)
    
    def _is_transient_error(self, error: Exception) -> bool:
        """
        Determine if an error is transient and should be retried.
        
        Args:
            error: The exception that occurred
            
        Returns:
            True if error is transient, False otherwise
        """
        # Common transient error patterns
        transient_patterns = [
            "timeout", "connection", "network", "rate limit", "throttle",
            "service unavailable", "temporary", "retry", "busy"
        ]
        
        error_str = str(error).lower()
        return any(pattern in error_str for pattern in transient_patterns)
    
    def retrieve_grouped_content(
        self, 
        similarity_threshold: float = 0.7,
        max_groups: int = 10,
        min_group_size: int = 2,
    ) -> List[SummaryInput]:
        """
        Retrieve grouped Claims and Sentences using vector similarity.
        
        This implements the non-agentic retrieval process described in
        on-writing_vault_documents.md using pg_vector_search.
        
        Args:
            similarity_threshold: Minimum cosine similarity for grouping
            max_groups: Maximum number of groups to return
            min_group_size: Minimum items per group
            
        Returns:
            List of SummaryInput objects representing semantic groups
        """
        if not self.neo4j_manager:
            logger.warning(
                "No Neo4j manager configured - cannot retrieve content",
                extra={
                    "service": "clarifai",
                    "filename.function_name": "agent.retrieve_grouped_content",
                }
            )
            return []
        
        start_time = time.time()
        
        try:
            # For now, implement a simple grouping strategy
            # In a full implementation, this would use sophisticated vector clustering
            
            # Get all Claims and Sentences from Neo4j with retry logic
            claims = self._retry_with_backoff(self._get_all_claims)
            sentences = self._retry_with_backoff(self._get_all_sentences)
            
            logger.info(
                "Retrieved claims and sentences for grouping",
                extra={
                    "service": "clarifai",
                    "filename.function_name": "agent.retrieve_grouped_content",
                    "claims_count": len(claims),
                    "sentences_count": len(sentences),
                }
            )
            
            # Simple grouping by file/conversation context for MVP
            # In production, this would use vector similarity clustering
            groups = self._group_by_conversation_context(claims, sentences, min_group_size)
            
            # Limit to max_groups
            if len(groups) > max_groups:
                groups = groups[:max_groups]
            
            processing_time = time.time() - start_time
            
            logger.info(
                "Created content groups for summarization",
                extra={
                    "service": "clarifai", 
                    "filename.function_name": "agent.retrieve_grouped_content",
                    "groups_count": len(groups),
                    "processing_time": processing_time,
                }
            )
            
            return groups
            
        except Exception as e:
            logger.error(
                "Failed to retrieve grouped content",
                extra={
                    "service": "clarifai",
                    "filename.function_name": "agent.retrieve_grouped_content",
                    "error": str(e),
                }
            )
            return []
    
    def _get_all_claims(self) -> List[Dict[str, Any]]:
        """Retrieve all Claim nodes from Neo4j."""
        try:
            query = """
            MATCH (c:Claim)
            RETURN c.id as id, c.text as text, c.entailed_score as entailed_score,
                   c.coverage_score as coverage_score, c.decontextualization_score as decontextualization_score,
                   c.version as version, c.timestamp as timestamp
            """
            result = self.neo4j_manager.execute_query(query)
            
            claims = []
            for record in result:
                claims.append({
                    'id': record['id'],
                    'text': record['text'],
                    'entailed_score': record['entailed_score'],
                    'coverage_score': record['coverage_score'], 
                    'decontextualization_score': record['decontextualization_score'],
                    'version': record['version'],
                    'timestamp': record['timestamp'],
                    'node_type': 'claim'
                })
            
            return claims
            
        except Exception as e:
            logger.error(
                "Failed to retrieve claims from Neo4j",
                extra={
                    "service": "clarifai",
                    "filename.function_name": "agent._get_all_claims",
                    "error": str(e),
                }
            )
            return []
    
    def _get_all_sentences(self) -> List[Dict[str, Any]]:
        """Retrieve all Sentence nodes from Neo4j."""
        try:
            query = """
            MATCH (s:Sentence)
            RETURN s.id as id, s.text as text, s.ambiguous as ambiguous,
                   s.verifiable as verifiable, s.version as version, s.timestamp as timestamp
            """
            result = self.neo4j_manager.execute_query(query)
            
            sentences = []
            for record in result:
                sentences.append({
                    'id': record['id'],
                    'text': record['text'],
                    'ambiguous': record['ambiguous'],
                    'verifiable': record['verifiable'],
                    'version': record['version'],
                    'timestamp': record['timestamp'],
                    'node_type': 'sentence'
                })
            
            return sentences
            
        except Exception as e:
            logger.error(
                "Failed to retrieve sentences from Neo4j",
                extra={
                    "service": "clarifai",
                    "filename.function_name": "agent._get_all_sentences",
                    "error": str(e),
                }
            )
            return []
    
    def _group_by_conversation_context(
        self, 
        claims: List[Dict[str, Any]], 
        sentences: List[Dict[str, Any]],
        min_group_size: int,
    ) -> List[SummaryInput]:
        """
        Simple grouping strategy by conversation context.
        
        In production, this would be replaced by vector similarity clustering.
        """
        # For MVP, we'll create groups of mixed claims and sentences
        # In practice, the grouping would use vector embeddings
        
        groups = []
        all_content = claims + sentences
        
        # Create groups of min_group_size items
        for i in range(0, len(all_content), min_group_size):
            group_items = all_content[i:i + min_group_size]
            
            if len(group_items) >= min_group_size:
                group_claims = [item for item in group_items if item.get('node_type') == 'claim']
                group_sentences = [item for item in group_items if item.get('node_type') == 'sentence']
                
                summary_input = SummaryInput(
                    claims=group_claims,
                    sentences=group_sentences,
                    group_context=f"Mixed content group {len(groups) + 1}"
                )
                groups.append(summary_input)
        
        return groups
    
    def generate_summary(self, summary_input: SummaryInput) -> SummaryResult:
        """
        Generate a summary from grouped Claims and Sentences.
        
        Args:
            summary_input: Grouped content to summarize
            
        Returns:
            SummaryResult with generated summary blocks
        """
        start_time = time.time()
        
        if not summary_input.all_texts:
            return SummaryResult(
                error="No content to summarize",
                processing_time=time.time() - start_time
            )
        
        try:
            # Create summary prompt
            prompt = self._create_summary_prompt(summary_input)
            
            logger.debug(
                "Generating summary for content items",
                extra={
                    "service": "clarifai",
                    "filename.function_name": "agent.generate_summary",
                    "content_count": len(summary_input.all_texts),
                }
            )
            
            # Generate summary using LLM with retry logic
            def _generate_llm_response():
                return self.llm.complete(prompt)
            
            response = self._retry_with_backoff(_generate_llm_response)
            summary_text = response.text.strip()
            
            # Create summary block
            summary_block = SummaryBlock(
                summary_text=summary_text,
                clarifai_id=generate_summary_id(),
                source_block_ids=summary_input.source_block_ids,
            )
            
            processing_time = time.time() - start_time
            
            result = SummaryResult(
                summary_blocks=[summary_block],
                source_file_context=summary_input.group_context,
                processing_time=processing_time,
                model_used=getattr(self.llm, 'model', 'unknown'),
            )
            
            logger.info(
                "Generated summary successfully",
                extra={
                    "service": "clarifai",
                    "filename.function_name": "agent.generate_summary",
                    "clarifai_id": summary_block.clarifai_id,
                    "processing_time": processing_time,
                }
            )
            
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            
            logger.error(
                "Failed to generate summary",
                extra={
                    "service": "clarifai",
                    "filename.function_name": "agent.generate_summary",
                    "error": str(e),
                    "processing_time": processing_time,
                }
            )
            
            return SummaryResult(
                error=str(e),
                processing_time=processing_time
            )
    
    def _create_summary_prompt(self, summary_input: SummaryInput) -> str:
        """
        Create a prompt for LLM summary generation.
        
        Args:
            summary_input: Content to summarize
            
        Returns:
            Formatted prompt string
        """
        prompt_parts = [
            "You are a specialized summarization agent for a knowledge management system.",
            "Your task is to create concise, informative summaries of related claims and statements.",
            "",
            "Please summarize the following content into coherent bullet points:",
            "- Focus on the key claims and factual statements",
            "- Group related concepts together",
            "- Keep each point concise but informative",
            "- Maintain the original meaning and context",
            "",
            "Content to summarize:"
        ]
        
        for i, text in enumerate(summary_input.all_texts, 1):
            prompt_parts.append(f"{i}. {text}")
        
        prompt_parts.extend([
            "",
            "Summary (as bullet points):"
        ])
        
        return "\n".join(prompt_parts)
    
    def write_summary_file(
        self, 
        summary_result: SummaryResult, 
        output_path: Union[str, Path],
        title: Optional[str] = None,
    ) -> bool:
        """
        Write summary result to a Tier 2 Markdown file using atomic writes.
        
        Args:
            summary_result: Generated summary to write
            output_path: Path where to write the file
            title: Optional title for the file
            
        Returns:
            True if successful, False otherwise
        """
        if not summary_result.is_successful:
            logger.error(
                "Cannot write summary file - generation failed",
                extra={
                    "service": "clarifai",
                    "filename.function_name": "agent.write_summary_file",
                    "output_path": str(output_path),
                    "error": summary_result.error,
                }
            )
            return False
        
        try:
            # Generate Markdown content
            markdown_content = summary_result.to_markdown(title=title)
            
            # Write atomically using existing function
            write_file_atomically(Path(output_path), markdown_content)
            
            logger.info(
                "Successfully wrote Tier 2 summary file",
                extra={
                    "service": "clarifai",
                    "filename.function_name": "agent.write_summary_file",
                    "output_path": str(output_path),
                    "summary_blocks_count": len(summary_result.summary_blocks),
                }
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "Failed to write summary file",
                extra={
                    "service": "clarifai",
                    "filename.function_name": "agent.write_summary_file",
                    "output_path": str(output_path),
                    "error": str(e),
                }
            )
            return False
    
    def process_and_generate_summaries(
        self, 
        output_dir: Optional[Union[str, Path]] = None,
        file_prefix: str = "tier2_summary",
    ) -> List[Path]:
        """
        Complete workflow: retrieve content, generate summaries, and write files.
        
        Args:
            output_dir: Directory to write summary files (uses config if not provided)
            file_prefix: Prefix for generated filenames
            
        Returns:
            List of paths to successfully written files
        """
        # Check if tier2_generation is enabled
        if not self._is_enabled():
            logger.warning(
                "Tier 2 summary generation is disabled in configuration - skipping",
                extra={
                    "service": "clarifai",
                    "filename.function_name": "agent.process_and_generate_summaries",
                }
            )
            return []
        
        if output_dir is None:
            # Use configured Tier 2 path
            vault_path = Path(self.config.paths.vault)
            tier2_path = self.config.paths.tier2
            output_dir = vault_path / tier2_path
        
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        start_time = time.time()
        written_files = []
        
        logger.info(
            "Starting Tier 2 summary generation process",
            extra={
                "service": "clarifai",
                "filename.function_name": "agent.process_and_generate_summaries",
                "output_dir": str(output_dir),
            }
        )
        
        try:
            # Retrieve grouped content
            groups = self.retrieve_grouped_content()
            
            if not groups:
                logger.warning(
                    "No content groups found for summarization",
                    extra={
                        "service": "clarifai",
                        "filename.function_name": "agent.process_and_generate_summaries",
                    }
                )
                return written_files
            
            # Generate summaries for each group
            for i, group in enumerate(groups):
                try:
                    # Generate summary
                    summary_result = self.generate_summary(group)
                    
                    if summary_result.is_successful:
                        # Create filename
                        filename = f"{file_prefix}_{i+1:03d}.md"
                        output_path = output_dir / filename
                        
                        # Write file
                        title = f"Tier 2 Summary {i+1}"
                        if self.write_summary_file(summary_result, output_path, title):
                            written_files.append(output_path)
                    else:
                        logger.warning(
                            "Failed to generate summary for group",
                            extra={
                                "service": "clarifai",
                                "filename.function_name": "agent.process_and_generate_summaries",
                                "group_index": i+1,
                                "error": summary_result.error,
                            }
                        )
                
                except Exception as e:
                    logger.error(
                        "Error processing group",
                        extra={
                            "service": "clarifai",
                            "filename.function_name": "agent.process_and_generate_summaries",
                            "group_index": i+1,
                            "error": str(e),
                        }
                    )
            
            processing_time = time.time() - start_time
            
            logger.info(
                "Completed Tier 2 summary generation",
                extra={
                    "service": "clarifai",
                    "filename.function_name": "agent.process_and_generate_summaries",
                    "groups_processed": len(groups),
                    "files_written": len(written_files),
                    "processing_time": processing_time,
                }
            )
            
            return written_files
            
        except Exception as e:
            processing_time = time.time() - start_time
            
            logger.error(
                "Failed to complete summary generation process",
                extra={
                    "service": "clarifai",
                    "filename.function_name": "agent.process_and_generate_summaries",
                    "error": str(e),
                    "processing_time": processing_time,
                }
            )
            
            return written_files
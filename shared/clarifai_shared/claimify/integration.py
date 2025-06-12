"""
Claimify to Neo4j integration utilities.

Provides functionality to convert Claimify pipeline results into Neo4j input data
and persist them to the knowledge graph.
"""

import logging
from typing import List, Tuple, Optional
import uuid
from datetime import datetime

from .data_models import ClaimCandidate, ClaimifyResult, SentenceChunk
from ..graph.data_models import ClaimInput, SentenceInput
from ..graph.manager import Neo4jGraphManager

logger = logging.getLogger(__name__)


class ClaimifyGraphIntegration:
    """
    Integrates Claimify pipeline results with Neo4j graph storage.
    
    Handles the conversion of Claimify output (ClaimCandidate objects) into
    Neo4j input data (ClaimInput, SentenceInput) and manages persistence
    to the knowledge graph.
    """
    
    def __init__(self, graph_manager: Neo4jGraphManager):
        """
        Initialize the integration with a graph manager.
        
        Args:
            graph_manager: Neo4jGraphManager instance for database operations
        """
        self.graph_manager = graph_manager
    
    def persist_claimify_results(self, results: List[ClaimifyResult]) -> Tuple[int, int, List[str]]:
        """
        Persist Claimify pipeline results to Neo4j.
        
        Args:
            results: List of ClaimifyResult objects from pipeline processing
            
        Returns:
            Tuple of (claims_created, sentences_created, errors)
        """
        claim_inputs = []
        sentence_inputs = []
        errors = []
        
        # Convert results to Neo4j input data
        for result in results:
            try:
                claims, sentences = self._convert_result_to_inputs(result)
                claim_inputs.extend(claims)
                sentence_inputs.extend(sentences)
            except Exception as e:
                error_msg = f"Failed to convert result for chunk {result.original_chunk.chunk_id}: {e}"
                errors.append(error_msg)
                logger.error(f"[integration.ClaimifyGraphIntegration.persist_claimify_results] {error_msg}")
        
        # Persist to Neo4j
        claims_created = 0
        sentences_created = 0
        
        if claim_inputs:
            success = self.graph_manager.create_claims_in_batch(claim_inputs)
            if success:
                claims_created = len(claim_inputs)
                logger.info(f"[integration.ClaimifyGraphIntegration.persist_claimify_results] Persisted {claims_created} claims")
            else:
                errors.append("Failed to persist claims to Neo4j")
        
        if sentence_inputs:
            success = self.graph_manager.create_sentences_in_batch(sentence_inputs)
            if success:
                sentences_created = len(sentence_inputs)
                logger.info(f"[integration.ClaimifyGraphIntegration.persist_claimify_results] Persisted {sentences_created} sentences")
            else:
                errors.append("Failed to persist sentences to Neo4j")
        
        return claims_created, sentences_created, errors
    
    def _convert_result_to_inputs(self, result: ClaimifyResult) -> Tuple[List[ClaimInput], List[SentenceInput]]:
        """
        Convert a single ClaimifyResult to Neo4j input objects.
        
        Args:
            result: ClaimifyResult from pipeline processing
            
        Returns:
            Tuple of (claim_inputs, sentence_inputs)
        """
        claim_inputs = []
        sentence_inputs = []
        
        # Handle successful processing with claims/sentences
        if result.was_processed and result.decomposition_result:
            # Convert valid claims to ClaimInput objects
            for claim_candidate in result.final_claims:
                claim_input = self._create_claim_input(claim_candidate, result.original_chunk)
                claim_inputs.append(claim_input)
            
            # Convert rejected candidates to SentenceInput objects
            for sentence_candidate in result.final_sentences:
                sentence_input = self._create_sentence_input(
                    sentence_candidate, 
                    result.original_chunk,
                    rejection_reason="Failed decomposition criteria"
                )
                sentence_inputs.append(sentence_input)
        
        # Handle sentences that were not selected for processing
        elif not result.was_processed:
            # Create a SentenceInput for the original chunk
            sentence_input = self._create_sentence_input_from_chunk(
                result.original_chunk,
                rejection_reason="Not selected by Selection agent"
            )
            sentence_inputs.append(sentence_input)
        
        return claim_inputs, sentence_inputs
    
    def _create_claim_input(self, claim_candidate: ClaimCandidate, source_chunk: SentenceChunk) -> ClaimInput:
        """
        Create a ClaimInput from a ClaimCandidate.
        
        Args:
            claim_candidate: Valid claim from decomposition
            source_chunk: Original sentence chunk
            
        Returns:
            ClaimInput object for Neo4j persistence
        """
        # Generate unique ID for the claim
        claim_id = f"claim_{uuid.uuid4().hex[:8]}"
        
        return ClaimInput(
            id=claim_id,
            text=claim_candidate.text,
            block_id=source_chunk.source_id,
            entailed_score=None,  # Will be set by evaluation agents in Sprint 7
            coverage_score=None,
            decontextualization_score=None,
            verifiable=claim_candidate.is_verifiable,
            self_contained=claim_candidate.is_self_contained,
            context_complete=claim_candidate.is_atomic,  # Using atomicity as context completeness
            version=1,
            timestamp=datetime.now()
        )
    
    def _create_sentence_input(
        self, 
        sentence_candidate: ClaimCandidate, 
        source_chunk: SentenceChunk,
        rejection_reason: Optional[str] = None
    ) -> SentenceInput:
        """
        Create a SentenceInput from a rejected ClaimCandidate.
        
        Args:
            sentence_candidate: Claim candidate that failed criteria
            source_chunk: Original sentence chunk
            rejection_reason: Why this became a sentence instead of claim
            
        Returns:
            SentenceInput object for Neo4j persistence
        """
        # Generate unique ID for the sentence
        sentence_id = f"sent_{uuid.uuid4().hex[:8]}"
        
        return SentenceInput(
            id=sentence_id,
            text=sentence_candidate.text,
            block_id=source_chunk.source_id,
            ambiguous=not sentence_candidate.is_self_contained,
            verifiable=sentence_candidate.is_verifiable,
            failed_decomposition=not sentence_candidate.is_atomic,
            rejection_reason=rejection_reason,
            version=1,
            timestamp=datetime.now()
        )
    
    def _create_sentence_input_from_chunk(
        self, 
        source_chunk: SentenceChunk,
        rejection_reason: Optional[str] = None
    ) -> SentenceInput:
        """
        Create a SentenceInput directly from a sentence chunk.
        
        Args:
            source_chunk: Original sentence chunk that wasn't processed
            rejection_reason: Why this wasn't processed
            
        Returns:
            SentenceInput object for Neo4j persistence
        """
        # Generate unique ID for the sentence
        sentence_id = f"sent_{uuid.uuid4().hex[:8]}"
        
        return SentenceInput(
            id=sentence_id,
            text=source_chunk.text,
            block_id=source_chunk.source_id,
            ambiguous=True,  # Assume ambiguous since it wasn't selected
            verifiable=False,  # Assume not verifiable since it wasn't selected
            failed_decomposition=False,  # Didn't reach decomposition
            rejection_reason=rejection_reason,
            version=1,
            timestamp=datetime.now()
        )


def create_graph_manager_from_config(config: dict) -> Neo4jGraphManager:
    """
    Create a Neo4jGraphManager from configuration.
    
    Args:
        config: Configuration dictionary with Neo4j settings
        
    Returns:
        Configured Neo4jGraphManager instance
    """
    neo4j_config = config.get('databases', {}).get('neo4j', {})
    
    manager = Neo4jGraphManager(config=neo4j_config)
    
    # Apply schema if not already applied
    manager.apply_core_schema()
    
    return manager
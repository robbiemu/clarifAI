"""
Concept processing integration for clarifai-core.

This module integrates concept detection and processing with the main 
clarifai-core pipeline, handling noun phrase extraction and concept 
candidate management.
"""

import logging
from typing import Dict, Any, List, Optional

from clarifai_shared.config import ClarifAIConfig
from clarifai_shared.concept_detection import ConceptDetector
from clarifai_shared.noun_phrase_extraction import NounPhraseExtractor
from clarifai_shared.noun_phrase_extraction.concept_candidates_store import ConceptCandidatesVectorStore
from clarifai_shared.concept_detection.models import ConceptAction, ConceptDetectionBatch

logger = logging.getLogger(__name__)


class ConceptProcessor:
    """
    Processes concept candidates and performs similarity-based concept detection.
    
    This class integrates noun phrase extraction, concept candidate storage,
    and hnswlib-based similarity detection to determine whether candidates
    should be merged or promoted.
    """
    
    def __init__(self, config: Optional[ClarifAIConfig] = None):
        """Initialize the concept processor."""
        self.config = config
        
        # Initialize components
        self.noun_phrase_extractor = NounPhraseExtractor(config)
        self.candidates_store = ConceptCandidatesVectorStore(config)
        self.concept_detector = ConceptDetector(config)
        
        logger.info(
            "Initialized ConceptProcessor",
            extra={
                "service": "clarifai-core",
                "filename.function_name": "concept_processor.ConceptProcessor.__init__",
            },
        )
    
    def process_block_for_concepts(
        self, 
        block: Dict[str, Any], 
        block_type: str = "claim"
    ) -> Dict[str, Any]:
        """
        Process a block to extract and analyze concept candidates.
        
        Args:
            block: The block dictionary with clarifai_id, semantic_text, etc.
            block_type: Type of block ("claim" or "summary")
            
        Returns:
            Dictionary with processing results and recommendations
        """
        clarifai_id = block.get("clarifai_id", "")
        semantic_text = block.get("semantic_text", "")
        
        logger.debug(
            f"Processing block for concepts: {clarifai_id}",
            extra={
                "service": "clarifai-core",
                "filename.function_name": "concept_processor.ConceptProcessor.process_block_for_concepts",
                "clarifai_id": clarifai_id,
                "block_type": block_type,
                "text_length": len(semantic_text),
            },
        )
        
        try:
            # Step 1: Extract noun phrases from the block
            extraction_result = self.noun_phrase_extractor.extract_from_text(
                text=semantic_text,
                source_node_id=clarifai_id,
                source_node_type=block_type,
                clarifai_id=clarifai_id
            )
            
            if not extraction_result.is_successful or not extraction_result.candidates:
                logger.debug(
                    f"No noun phrases extracted from block {clarifai_id}",
                    extra={
                        "service": "clarifai-core",
                        "filename.function_name": "concept_processor.ConceptProcessor.process_block_for_concepts",
                        "clarifai_id": clarifai_id,
                        "extraction_error": extraction_result.error,
                    },
                )
                return {
                    "success": True,
                    "clarifai_id": clarifai_id,
                    "candidates_extracted": 0,
                    "candidates_stored": 0,
                    "concept_actions": [],
                    "message": "No noun phrases extracted"
                }
            
            # Step 2: Store candidates in vector store
            stored_count = self.candidates_store.store_candidates(extraction_result.candidates)
            
            # Step 3: Perform concept detection on the extracted candidates
            detection_batch = self.concept_detector.process_candidates_batch(
                extraction_result.candidates
            )
            
            # Step 4: Update candidate statuses based on detection results
            updated_candidates = self._update_candidate_statuses(detection_batch)
            
            # Prepare results summary
            results = {
                "success": True,
                "clarifai_id": clarifai_id,
                "block_type": block_type,
                "candidates_extracted": len(extraction_result.candidates),
                "candidates_stored": stored_count,
                "concept_actions": [],
                "merged_count": detection_batch.merged_count,
                "promoted_count": detection_batch.promoted_count,
                "processing_time": detection_batch.processing_time,
                "updated_candidates": updated_candidates
            }
            
            # Add concept action recommendations
            for result in detection_batch.results:
                action_info = {
                    "candidate_text": result.candidate_text,
                    "action": result.action.value,
                    "confidence": result.confidence,
                    "reason": result.reason,
                    "best_match": None
                }
                
                if result.best_match:
                    action_info["best_match"] = {
                        "text": result.best_match.matched_text,
                        "similarity": result.best_match.similarity_score
                    }
                
                results["concept_actions"].append(action_info)
            
            logger.info(
                f"Processed {len(extraction_result.candidates)} concept candidates from block {clarifai_id}: "
                f"{detection_batch.merged_count} merged, {detection_batch.promoted_count} promoted",
                extra={
                    "service": "clarifai-core",
                    "filename.function_name": "concept_processor.ConceptProcessor.process_block_for_concepts",
                    "clarifai_id": clarifai_id,
                    "candidates_extracted": len(extraction_result.candidates),
                    "merged_count": detection_batch.merged_count,
                    "promoted_count": detection_batch.promoted_count,
                },
            )
            
            return results
            
        except Exception as e:
            logger.error(
                f"Error processing block for concepts: {e}",
                extra={
                    "service": "clarifai-core",
                    "filename.function_name": "concept_processor.ConceptProcessor.process_block_for_concepts",
                    "clarifai_id": clarifai_id,
                    "error": str(e),
                },
            )
            return {
                "success": False,
                "clarifai_id": clarifai_id,
                "error": str(e),
                "candidates_extracted": 0,
                "candidates_stored": 0,
                "concept_actions": []
            }
    
    def _update_candidate_statuses(self, detection_batch: ConceptDetectionBatch) -> List[Dict[str, Any]]:
        """
        Update the status of candidates based on detection results.
        
        In a full implementation, this would update the concept_candidates
        table to mark items as "merged" or "promoted". For now, we just
        prepare the update information.
        
        Args:
            detection_batch: Results from concept detection
            
        Returns:
            List of candidate updates to be applied
        """
        updates = []
        
        for result in detection_batch.results:
            update = {
                "candidate_id": result.candidate_id,
                "candidate_text": result.candidate_text,
                "new_status": result.action.value,
                "confidence": result.confidence,
                "reason": result.reason
            }
            
            if result.action == ConceptAction.MERGED and result.best_match:
                update["merged_with"] = {
                    "matched_id": result.best_match.matched_candidate_id,
                    "matched_text": result.best_match.matched_text,
                    "similarity_score": result.best_match.similarity_score
                }
            
            updates.append(update)
        
        logger.debug(
            f"Prepared {len(updates)} candidate status updates",
            extra={
                "service": "clarifai-core",
                "filename.function_name": "concept_processor.ConceptProcessor._update_candidate_statuses",
                "updates_count": len(updates),
            },
        )
        
        return updates
    
    def build_concept_index(self, force_rebuild: bool = False) -> int:
        """
        Build or rebuild the concept detection index.
        
        Args:
            force_rebuild: Whether to force rebuild even if index exists
            
        Returns:
            Number of items added to the index
        """
        logger.info(
            "Building concept detection index",
            extra={
                "service": "clarifai-core",
                "filename.function_name": "concept_processor.ConceptProcessor.build_concept_index",
                "force_rebuild": force_rebuild,
            },
        )
        
        try:
            items_added = self.concept_detector.build_index_from_candidates(force_rebuild)
            
            logger.info(
                f"Built concept detection index with {items_added} items",
                extra={
                    "service": "clarifai-core",
                    "filename.function_name": "concept_processor.ConceptProcessor.build_concept_index",
                    "items_added": items_added,
                },
            )
            
            return items_added
            
        except Exception as e:
            logger.error(
                f"Error building concept index: {e}",
                extra={
                    "service": "clarifai-core",
                    "filename.function_name": "concept_processor.ConceptProcessor.build_concept_index",
                    "error": str(e),
                },
            )
            raise
    
    def get_concept_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about concept candidates and detection.
        
        Returns:
            Dictionary with various statistics
        """
        try:
            # Get candidates by status
            pending_candidates = self.candidates_store.get_candidates_by_status("pending")
            merged_candidates = self.candidates_store.get_candidates_by_status("merged")
            promoted_candidates = self.candidates_store.get_candidates_by_status("promoted")
            
            stats = {
                "total_candidates": len(pending_candidates) + len(merged_candidates) + len(promoted_candidates),
                "pending_candidates": len(pending_candidates),
                "merged_candidates": len(merged_candidates),
                "promoted_candidates": len(promoted_candidates),
                "index_size": len(self.concept_detector.id_to_metadata),
                "similarity_threshold": self.concept_detector.similarity_threshold
            }
            
            logger.debug(
                f"Concept statistics: {stats}",
                extra={
                    "service": "clarifai-core",
                    "filename.function_name": "concept_processor.ConceptProcessor.get_concept_statistics",
                    **stats
                },
            )
            
            return stats
            
        except Exception as e:
            logger.error(
                f"Error getting concept statistics: {e}",
                extra={
                    "service": "clarifai-core",
                    "filename.function_name": "concept_processor.ConceptProcessor.get_concept_statistics",
                    "error": str(e),
                },
            )
            return {
                "error": str(e),
                "total_candidates": 0,
                "pending_candidates": 0,
                "merged_candidates": 0,
                "promoted_candidates": 0,
                "index_size": 0
            }
"""
Main orchestrator for claim-concept linking.

This module provides the main ClaimConceptLinker class that coordinates
the full linking process, from fetching claims to updating Markdown files.
"""

import logging
from typing import List, Optional, Dict, Any

from ..config import aclaraiConfig, load_config
from .agent import ClaimConceptLinkerAgent
from .neo4j_operations import ClaimConceptNeo4jManager
from .markdown_updater import Tier2MarkdownUpdater
from .models import (
    ClaimConceptPair,
    ClaimConceptLinkResult,
    ConceptCandidate,
)

logger = logging.getLogger(__name__)


class ClaimConceptLinker:
    """
    Main orchestrator for linking claims to concepts.

    This class coordinates the full process of:
    1. Fetching unlinked claims
    2. Finding candidate concepts (currently blocked - needs concepts vector store)
    3. Classifying relationships with LLM
    4. Creating Neo4j relationships
    5. Updating Tier 2 Markdown files
    """

    def __init__(self, config: Optional[aclaraiConfig] = None):
        """
        Initialize the claim-concept linker.

        Args:
            config: aclarai configuration (loads default if None)
        """
        self.config = config or load_config()

        # Initialize components
        self.agent = ClaimConceptLinkerAgent(config)
        self.neo4j_manager = ClaimConceptNeo4jManager(config)
        self.markdown_updater = Tier2MarkdownUpdater(config)

        logger.info(
            "Initialized ClaimConceptLinker",
            extra={
                "service": "aclarai",
                "filename.function_name": "claim_concept_linking.ClaimConceptLinker.__init__",
            },
        )

    def link_claims_to_concepts(
        self,
        max_claims: int = 100,
        similarity_threshold: float = 0.7,
        strength_threshold: float = 0.5,
    ) -> Dict[str, Any]:
        """
        Execute the full claim-concept linking process.

        Args:
            max_claims: Maximum number of claims to process
            similarity_threshold: Minimum similarity for concept candidates
            strength_threshold: Minimum strength for creating relationships

        Returns:
            Dictionary with processing statistics and results
        """
        logger.info(
            "Starting claim-concept linking process",
            extra={
                "service": "aclarai",
                "filename.function_name": "claim_concept_linking.ClaimConceptLinker.link_claims_to_concepts",
                "max_claims": max_claims,
                "similarity_threshold": similarity_threshold,
                "strength_threshold": strength_threshold,
            },
        )

        stats = {
            "claims_fetched": 0,
            "concepts_available": 0,
            "pairs_analyzed": 0,
            "links_created": 0,
            "files_updated": 0,
            "errors": [],
        }

        try:
            # Step 1: Fetch unlinked claims
            claims = self.neo4j_manager.fetch_unlinked_claims(limit=max_claims)
            stats["claims_fetched"] = len(claims)

            if not claims:
                logger.info(
                    "No unlinked claims found",
                    extra={
                        "service": "aclarai",
                        "filename.function_name": "claim_concept_linking.ClaimConceptLinker.link_claims_to_concepts",
                    },
                )
                return stats

            # Step 2: Fetch available concepts
            concepts = self.neo4j_manager.fetch_all_concepts()
            stats["concepts_available"] = len(concepts)

            if not concepts:
                logger.warning(
                    "No concepts available for linking - this is expected if Tier 3 creation task hasn't run yet",
                    extra={
                        "service": "aclarai",
                        "filename.function_name": "claim_concept_linking.ClaimConceptLinker.link_claims_to_concepts",
                    },
                )
                return stats

            # Step 3: Process claim-concept pairs
            successful_links = []

            for claim in claims:
                # For each claim, find candidate concepts
                # NOTE: This is where vector similarity search would normally happen
                # For now, we'll use a simple text matching as fallback
                candidate_concepts = self._find_candidate_concepts_fallback(
                    claim, concepts, similarity_threshold
                )

                # Classify relationships for each candidate
                for candidate in candidate_concepts:
                    pair = self._create_claim_concept_pair(claim, candidate)
                    stats["pairs_analyzed"] += 1

                    # Get LLM classification
                    classification = self.agent.classify_relationship(pair)

                    if classification and classification.strength >= strength_threshold:
                        # Convert to link result
                        link_result = self._create_link_result(pair, classification)

                        # Create Neo4j relationship
                        if self.neo4j_manager.create_claim_concept_relationship(
                            link_result
                        ):
                            successful_links.append(link_result)
                            stats["links_created"] += 1
                        else:
                            stats["errors"].append(
                                f"Failed to create relationship for {pair.claim_id} -> {pair.concept_id}"
                            )

            # Step 4: Update Markdown files
            if successful_links:
                markdown_stats = self.markdown_updater.update_files_with_links(
                    successful_links
                )
                stats["files_updated"] = markdown_stats["files_updated"]
                stats["errors"].extend(markdown_stats["errors"])

            logger.info(
                "Completed claim-concept linking",
                extra={
                    "service": "aclarai",
                    "filename.function_name": "claim_concept_linking.ClaimConceptLinker.link_claims_to_concepts",
                    **stats,
                },
            )

        except Exception as e:
            error_msg = f"Fatal error in claim-concept linking: {e}"
            stats["errors"].append(error_msg)
            logger.error(
                error_msg,
                extra={
                    "service": "aclarai",
                    "filename.function_name": "claim_concept_linking.ClaimConceptLinker.link_claims_to_concepts",
                    "error": str(e),
                },
            )

        return stats

    def _find_candidate_concepts_fallback(
        self, claim: Dict[str, Any], concepts: List[Dict[str, Any]], threshold: float
    ) -> List[ConceptCandidate]:
        """
        Fallback method for finding candidate concepts using simple text matching.

        This is a placeholder for the vector similarity search that will be
        available once the concepts vector store is implemented.

        Args:
            claim: Claim dictionary
            concepts: List of available concepts
            threshold: Similarity threshold (unused in fallback)

        Returns:
            List of concept candidates
        """
        candidates = []
        claim_text_lower = claim["text"].lower()

        # Simple keyword matching as fallback
        for concept in concepts:
            concept_text_lower = concept["text"].lower()

            # Check if concept text appears in claim text
            if concept_text_lower in claim_text_lower:
                candidate = ConceptCandidate(
                    concept_id=concept["id"],
                    concept_text=concept["text"],
                    similarity_score=0.8,  # Fixed score for keyword match
                    source_node_id=concept.get("source_node_id"),
                    source_node_type=concept.get("source_node_type"),
                    aclarai_id=concept.get("aclarai_id"),
                )
                candidates.append(candidate)

        # Limit to top candidates
        return candidates[:5]  # Max 5 candidates per claim

    def _create_claim_concept_pair(
        self, claim: Dict[str, Any], candidate: ConceptCandidate
    ) -> ClaimConceptPair:
        """
        Create a ClaimConceptPair from claim data and concept candidate.

        Args:
            claim: Claim dictionary from Neo4j
            candidate: Concept candidate

        Returns:
            ClaimConceptPair for classification
        """
        # Get additional context if available
        context = self.neo4j_manager.get_claim_context(claim["id"])

        return ClaimConceptPair(
            claim_id=claim["id"],
            claim_text=claim["text"],
            concept_id=candidate.concept_id,
            concept_text=candidate.concept_text,
            source_sentence=context.get("source_block_text") if context else None,
            summary_block=context.get("summary_text") if context else None,
            entailed_score=claim.get("entailed_score"),
            coverage_score=claim.get("coverage_score"),
            decontextualization_score=claim.get("decontextualization_score"),
        )

    def _create_link_result(
        self,
        pair: ClaimConceptPair,
        classification: Any,  # AgentClassificationResult
    ) -> ClaimConceptLinkResult:
        """
        Create a ClaimConceptLinkResult from classification.

        Args:
            pair: The claim-concept pair
            classification: LLM classification result

        Returns:
            ClaimConceptLinkResult for Neo4j storage
        """
        # Convert string relation to enum
        relationship = classification.to_relationship_type()
        if not relationship:
            raise ValueError(f"Invalid relationship type: {classification.relation}")

        return ClaimConceptLinkResult(
            claim_id=pair.claim_id,
            concept_id=pair.concept_id,
            relationship=relationship,
            strength=classification.strength,
            # Copy scores from the claim (may be null during Sprint 5)
            entailed_score=pair.entailed_score,
            coverage_score=pair.coverage_score,
            agent_model=self.agent.model_name,
        )

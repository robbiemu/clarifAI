"""
Claim-Concept Linking Orchestrator.

This module contains the ClaimConceptLinker class that orchestrates the process
of linking Claims to Concepts using vector similarity search and LLM classification.
"""

import logging
from typing import Optional, List, Dict, Any

from ..config import aclaraiConfig
from ..graph.neo4j_manager import Neo4jGraphManager
from ..noun_phrase_extraction.concept_candidates_store import (
    ConceptCandidatesVectorStore,
)
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
    Orchestrator for linking Claims to Concepts in the knowledge graph.

    This class provides the main coordination logic for:
    1. Querying for Claims that need linking
    2. Finding candidate Concepts via vector similarity
    3. Using LLM classification to determine relationship types
    4. Creating relationships in Neo4j
    5. Updating Markdown files with wikilinks
    """

    def __init__(
        self,
        config: Optional[aclaraiConfig] = None,
        neo4j_manager: Optional[Neo4jGraphManager] = None,
        vector_store: Optional[ConceptCandidatesVectorStore] = None,
    ):
        """
        Initialize the ClaimConceptLinker.

        Args:
            config: aclarai configuration (loads default if None)
            neo4j_manager: Neo4j manager instance (creates real one if None)
            vector_store: Vector store instance (creates real one if None)
        """
        # Only create real services if no mocks provided
        if neo4j_manager is None or vector_store is None:
            if config is None:
                from ..config import load_config

                config = load_config(validate=False)

        self.config = config
        self.neo4j_manager = neo4j_manager or Neo4jGraphManager(config)
        self.vector_store = vector_store or ConceptCandidatesVectorStore(config)

        # Initialize additional components for full implementation
        self.agent = ClaimConceptLinkerAgent(config)
        self.custom_neo4j_manager = ClaimConceptNeo4jManager(config)
        self.markdown_updater = Tier2MarkdownUpdater(config)

        logger.info(
            "claim_concept_linking.orchestrator.ClaimConceptLinker.__init__: "
            "ClaimConceptLinker initialized",
            extra={
                "service": "aclarai-core",
                "filename.function_name": "orchestrator.ClaimConceptLinker.__init__",
                "neo4j_manager_type": type(self.neo4j_manager).__name__,
                "vector_store_type": type(self.vector_store).__name__,
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
            "claim_concept_linking.orchestrator.ClaimConceptLinker.link_claims_to_concepts: "
            "Starting claim-concept linking process",
            extra={
                "service": "aclarai-core",
                "filename.function_name": "orchestrator.ClaimConceptLinker.link_claims_to_concepts",
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
            claims = self.custom_neo4j_manager.fetch_unlinked_claims(limit=max_claims)
            stats["claims_fetched"] = len(claims)

            if not claims:
                logger.info(
                    "No unlinked claims found",
                    extra={
                        "service": "aclarai-core",
                        "filename.function_name": "orchestrator.ClaimConceptLinker.link_claims_to_concepts",
                    },
                )
                return stats

            # Step 2: Try to use vector store for concept candidates, fallback to simple approach
            try:
                # Use the real concepts vector store
                concepts = self._get_concepts_from_vector_store()
                stats["concepts_available"] = len(concepts)
            except Exception as e:
                logger.warning(
                    "Vector store unavailable, using fallback concept fetching",
                    extra={
                        "service": "aclarai-core",
                        "filename.function_name": "orchestrator.ClaimConceptLinker.link_claims_to_concepts",
                        "error": str(e),
                    },
                )
                # Fallback to Neo4j direct fetch
                concepts = self.custom_neo4j_manager.fetch_all_concepts()
                stats["concepts_available"] = len(concepts)

            if not concepts:
                logger.warning(
                    "No concepts available for linking - this is expected if Tier 3 creation task hasn't run yet",
                    extra={
                        "service": "aclarai-core",
                        "filename.function_name": "orchestrator.ClaimConceptLinker.link_claims_to_concepts",
                    },
                )
                return stats

            # Step 3: Process claim-concept pairs
            successful_links = []

            for claim in claims:
                # Find candidate concepts using vector similarity or fallback
                candidate_concepts = self._find_candidate_concepts(
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
                        if self.custom_neo4j_manager.create_claim_concept_relationship(
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
                    "service": "aclarai-core",
                    "filename.function_name": "orchestrator.ClaimConceptLinker.link_claims_to_concepts",
                    **stats,
                },
            )

        except Exception as e:
            error_msg = f"Fatal error in claim-concept linking: {e}"
            stats["errors"].append(error_msg)
            logger.error(
                error_msg,
                extra={
                    "service": "aclarai-core",
                    "filename.function_name": "orchestrator.ClaimConceptLinker.link_claims_to_concepts",
                    "error": str(e),
                },
            )

        return stats

    def _get_concepts_from_vector_store(self) -> List[Dict[str, Any]]:
        """
        Get all concepts from the vector store.

        Returns:
            List of concept dictionaries
        """
        # This would use the vector store to get all available concepts
        # For now, return empty list if not available
        return []

    def _find_candidate_concepts(
        self, claim: Dict[str, Any], concepts: List[Dict[str, Any]], threshold: float
    ) -> List[ConceptCandidate]:
        """
        Find candidate concepts using vector similarity or fallback text matching.

        Args:
            claim: Claim dictionary
            concepts: List of available concepts (from vector store or Neo4j)
            threshold: Similarity threshold

        Returns:
            List of concept candidates
        """
        # Try to use vector store for similarity search
        try:
            if hasattr(self.vector_store, "find_similar_candidates"):
                similar_candidates = self.vector_store.find_similar_candidates(
                    claim["text"], top_k=5
                )
                # Convert to ConceptCandidate objects
                candidates = []
                for candidate_data in similar_candidates:
                    candidate = ConceptCandidate(
                        concept_id=candidate_data.get(
                            "concept_id", candidate_data.get("id")
                        ),
                        concept_text=candidate_data.get(
                            "concept_text", candidate_data.get("text")
                        ),
                        similarity_score=candidate_data.get(
                            "similarity_score", candidate_data.get("score", 0.0)
                        ),
                        source_node_id=candidate_data.get("source_node_id"),
                        source_node_type=candidate_data.get("source_node_type"),
                        aclarai_id=candidate_data.get("aclarai_id"),
                    )
                    candidates.append(candidate)
                return candidates
        except Exception as e:
            logger.warning(
                "Vector similarity search failed, using fallback text matching",
                extra={
                    "service": "aclarai-core",
                    "filename.function_name": "orchestrator.ClaimConceptLinker._find_candidate_concepts",
                    "error": str(e),
                },
            )

        # Fallback to simple text matching
        return self._find_candidate_concepts_fallback(claim, concepts, threshold)

    def _find_candidate_concepts_fallback(
        self, claim: Dict[str, Any], concepts: List[Dict[str, Any]], threshold: float
    ) -> List[ConceptCandidate]:
        """
        Fallback method for finding candidate concepts using simple text matching.

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
        context = self.custom_neo4j_manager.get_claim_context(claim["id"])

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

    def get_unlinked_claims(self) -> List[Dict[str, Any]]:
        """
        Query for Claims that need linking to Concepts.

        Returns:
            List of Claim data dictionaries
        """
        return self.custom_neo4j_manager.fetch_unlinked_claims()

    def find_candidate_concepts(
        self, claim_text: str, top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find candidate Concepts for a given Claim using vector similarity.

        Args:
            claim_text: The text of the claim to find concepts for
            top_k: Maximum number of candidates to return

        Returns:
            List of candidate concept data with similarity scores
        """
        # This would use the vector_store to find similar concepts
        return self.vector_store.find_similar_candidates(claim_text, top_k=top_k)

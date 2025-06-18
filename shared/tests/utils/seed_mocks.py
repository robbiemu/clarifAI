"""
Mock data seeding utilities.

This module provides functions to populate mock services with a predictable
"golden set" of concept data for testing and development.
"""

import logging
from typing import Tuple
import uuid

from aclarai_shared.graph.models import ConceptInput, ClaimInput
from aclarai_shared.noun_phrase_extraction.models import NounPhraseCandidate
from ..mocks.mock_neo4j_manager import MockNeo4jGraphManager
from ..mocks.mock_vector_store import MockVectorStore

logger = logging.getLogger(__name__)


def get_seeded_mock_services() -> Tuple[MockNeo4jGraphManager, MockVectorStore]:
    """
    Get mock services populated with a predictable golden dataset.

    This function creates and populates MockNeo4jGraphManager and MockVectorStore
    instances with a small set of concept data suitable for testing claim-concept
    linking development.

    Returns:
        Tuple of (neo4j_manager, vector_store) populated with golden data
    """
    logger.info(
        "seed_mocks.get_seeded_mock_services: Creating seeded mock services",
        extra={
            "service": "aclarai-test",
            "filename.function_name": "seed_mocks.get_seeded_mock_services",
        },
    )

    # Create mock services
    neo4j_manager = MockNeo4jGraphManager()
    vector_store = MockVectorStore()

    # Define golden dataset of concepts
    golden_concepts = [
        "Machine Learning",
        "GPU Error",
        "CUDA Error",
        "Deep Learning",
        "Neural Networks",
        "Data Science",
        "Python Programming",
        "Database Optimization",
        "API Development",
        "Software Architecture",
    ]

    # Create concept candidates for vector store
    concept_candidates = []
    concept_inputs = []

    for i, concept_text in enumerate(golden_concepts):
        candidate_id = f"candidate_{uuid.uuid4().hex[:8]}"
        concept_id = f"concept_{uuid.uuid4().hex[:8]}"

        # Create concept candidate for vector store
        candidate = NounPhraseCandidate(
            text=concept_text,
            normalized_text=concept_text.lower(),
            source_node_id=f"source_{i}",
            source_node_type="Summary",
            aclarai_id=f"aclarai_{i}",
        )
        concept_candidates.append(candidate)

        # Create concept input for Neo4j
        concept_input = ConceptInput(
            text=concept_text,
            source_candidate_id=candidate_id,
            source_node_id=f"source_{i}",
            source_node_type="Summary",
            aclarai_id=f"aclarai_{i}",
            concept_id=concept_id,
        )
        concept_inputs.append(concept_input)

    # Populate vector store with candidates
    vector_store.store_candidates(concept_candidates)

    # Populate Neo4j with concepts
    neo4j_manager.create_concepts(concept_inputs)

    # Create some sample claims for testing
    claim_inputs = [
        ClaimInput(
            text="The model failed to train due to GPU memory issues",
            block_id="block_1",
            claim_id="claim_1",
        ),
        ClaimInput(
            text="Deep learning requires large datasets for good performance",
            block_id="block_2",
            claim_id="claim_2",
        ),
        ClaimInput(
            text="CUDA 12.3 compatibility issues with the current driver",
            block_id="block_3",
            claim_id="claim_3",
        ),
    ]

    neo4j_manager.create_claims(claim_inputs)

    logger.info(
        "seed_mocks.get_seeded_mock_services: Mock services seeded successfully",
        extra={
            "service": "aclarai-test",
            "filename.function_name": "seed_mocks.get_seeded_mock_services",
            "concepts_count": len(golden_concepts),
            "claims_count": len(claim_inputs),
            "vector_documents": len(vector_store.documents),
            "neo4j_concepts": len(neo4j_manager.concepts),
            "neo4j_claims": len(neo4j_manager.claims),
        },
    )

    return neo4j_manager, vector_store

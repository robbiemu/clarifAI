#!/usr/bin/env python3
"""
Demonstration script for the claim-concept linking system.

This script shows how to use the ClaimConceptLinker to link claims to concepts.
It can run in simulation mode (with mocked data) when the concepts vector store
is not yet available, or with real data once the Tier 3 creation task is complete.

Usage:
    python demo_claim_concept_linking.py [--simulation]
"""

import argparse
import logging
import sys
from typing import Dict, Any, List
from datetime import datetime

# Set up basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

try:
    from aclarai_shared.claim_concept_linking import (
        ClaimConceptLinker,
        ClaimConceptLinkResult,
        RelationshipType,
    )
    from aclarai_shared.config import load_config
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure to run this script from the repository root with:")
    print("uv run python shared/aclarai_shared/scripts/demo_claim_concept_linking.py")
    sys.exit(1)

logger = logging.getLogger(__name__)


class MockClaimConceptLinker:
    """
    Mock implementation for demonstration when concepts vector store is not available.
    """
    
    def __init__(self):
        logger.info("Initialized MockClaimConceptLinker for simulation mode")
    
    def link_claims_to_concepts(
        self,
        max_claims: int = 100,
        similarity_threshold: float = 0.7,
        strength_threshold: float = 0.5,
    ) -> Dict[str, Any]:
        """Simulate the claim-concept linking process with mock data."""
        
        logger.info("Starting simulated claim-concept linking process")
        
        # Mock some example results
        mock_results = {
            "claims_fetched": 5,
            "concepts_available": 12,
            "pairs_analyzed": 8,
            "links_created": 3,
            "files_updated": 2,
            "errors": [],
        }
        
        # Simulate some processing time
        import time
        time.sleep(1)
        
        logger.info("Simulated linking process completed")
        logger.info(f"Results: {mock_results}")
        
        return mock_results


def demonstrate_models():
    """Demonstrate the data models used in claim-concept linking."""
    
    print("\n" + "="*60)
    print("CLAIM-CONCEPT LINKING DATA MODELS DEMONSTRATION")
    print("="*60)
    
    # Import the models
    from aclarai_shared.claim_concept_linking.models import (
        ClaimConceptPair,
        ClaimConceptLinkResult,
        RelationshipType,
        AgentClassificationResult,
        ConceptCandidate,
    )
    
    print("\n1. ClaimConceptPair - Represents a claim-concept pair for analysis:")
    pair = ClaimConceptPair(
        claim_id="claim_123",
        claim_text="OpenAI released GPT-4 in March 2023",
        concept_id="concept_456", 
        concept_text="artificial intelligence models",
        source_sentence="The company announced the new model to the public.",
        entailed_score=0.92,
        coverage_score=0.85
    )
    print(f"  Claim: {pair.claim_text}")
    print(f"  Concept: {pair.concept_text}")
    print(f"  Scores: entailed={pair.entailed_score}, coverage={pair.coverage_score}")
    
    print("\n2. RelationshipType - Types of claim-concept relationships:")
    for rel_type in RelationshipType:
        print(f"  - {rel_type.value}")
    
    print("\n3. ClaimConceptLinkResult - Successful linking result:")
    result = ClaimConceptLinkResult(
        claim_id=pair.claim_id,
        concept_id=pair.concept_id,
        relationship=RelationshipType.SUPPORTS_CONCEPT,
        strength=0.89,
        entailed_score=pair.entailed_score,
        coverage_score=pair.coverage_score,
        agent_model="gpt-4o"
    )
    print(f"  Relationship: {result.relationship.value}")
    print(f"  Strength: {result.strength}")
    print(f"  Created: {result.classified_at}")
    
    print("\n4. Neo4j Properties:")
    props = result.to_neo4j_properties()
    for key, value in props.items():
        print(f"  {key}: {value}")


def demonstrate_linking(simulation_mode: bool = False):
    """Demonstrate the claim-concept linking process."""
    
    print("\n" + "="*60)
    print("CLAIM-CONCEPT LINKING PROCESS DEMONSTRATION")
    print("="*60)
    
    if simulation_mode:
        print("\nRunning in SIMULATION MODE (concepts vector store not available)")
        linker = MockClaimConceptLinker()
    else:
        print("\nRunning with REAL DATA (requires concepts vector store)")
        try:
            linker = ClaimConceptLinker()
        except Exception as e:
            print(f"\nError initializing ClaimConceptLinker: {e}")
            print("Falling back to simulation mode...")
            linker = MockClaimConceptLinker()
            simulation_mode = True
    
    print(f"\nParameters:")
    print(f"  max_claims: 10")
    print(f"  similarity_threshold: 0.7")  
    print(f"  strength_threshold: 0.5")
    
    print(f"\nStarting linking process...")
    
    try:
        results = linker.link_claims_to_concepts(
            max_claims=10,
            similarity_threshold=0.7,
            strength_threshold=0.5
        )
        
        print(f"\nRESULTS:")
        print(f"  Claims fetched: {results['claims_fetched']}")
        print(f"  Concepts available: {results['concepts_available']}")
        print(f"  Pairs analyzed: {results['pairs_analyzed']}")
        print(f"  Links created: {results['links_created']}")
        print(f"  Files updated: {results['files_updated']}")
        print(f"  Errors: {len(results.get('errors', []))}")
        
        if results.get('errors'):
            print(f"\nErrors encountered:")
            for error in results['errors']:
                print(f"  - {error}")
                
        if simulation_mode:
            print(f"\n⚠️  This was a simulation. To run with real data:")
            print(f"    1. Ensure the concepts vector store is populated")
            print(f"    2. Configure Neo4j connection in aclarai.config.yaml")
            print(f"    3. Set up LLM API key (OpenAI recommended)")
            print(f"    4. Run without --simulation flag")
        
    except Exception as e:
        print(f"\nError during linking process: {e}")
        logger.exception("Detailed error information")


def demonstrate_configuration():
    """Demonstrate configuration requirements."""
    
    print("\n" + "="*60)
    print("CONFIGURATION REQUIREMENTS")
    print("="*60)
    
    print("\nRequired configuration in aclarai.config.yaml:")
    print("""
llm:
  provider: "openai"
  model: "gpt-4o"
  api_key: "${OPENAI_API_KEY}"

neo4j:
  uri: "bolt://localhost:7687"
  username: "neo4j"
  password: "${NEO4J_PASSWORD}"

vault_path: "./vault"
""")
    
    print("\nRequired environment variables:")
    print("  - OPENAI_API_KEY: Your OpenAI API key")
    print("  - NEO4J_PASSWORD: Neo4j database password")
    
    print("\nPrerequisites:")
    print("  - Neo4j database with (:Claim) and (:Concept) nodes")
    print("  - Concepts vector store populated by Tier 3 creation task")
    print("  - Vault directory with Tier 2 Markdown files")


def main():
    """Main demonstration function."""
    
    parser = argparse.ArgumentParser(description="Demonstrate claim-concept linking system")
    parser.add_argument(
        "--simulation", 
        action="store_true",
        help="Run in simulation mode with mock data"
    )
    
    args = parser.parse_args()
    
    print("ACLARAI CLAIM-CONCEPT LINKING SYSTEM DEMONSTRATION")
    print("=" * 60)
    print("This script demonstrates the claim-concept linking system")
    print("that creates semantic relationships between (:Claim) and (:Concept) nodes.")
    
    try:
        # Demonstrate the data models
        demonstrate_models()
        
        # Demonstrate the linking process
        demonstrate_linking(simulation_mode=args.simulation)
        
        # Show configuration requirements
        demonstrate_configuration()
        
        print("\n" + "="*60)
        print("DEMONSTRATION COMPLETE")
        print("="*60)
        print("\nFor more information, see:")
        print("  - docs/components/claim_concept_linking.md")
        print("  - shared/tests/claim_concept_linking/ (for examples)")
        
    except KeyboardInterrupt:
        print("\n\nDemonstration interrupted by user")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        logger.exception("Detailed error information")
        sys.exit(1)


if __name__ == "__main__":
    main()
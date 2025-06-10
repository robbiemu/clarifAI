#!/usr/bin/env python3
"""
Example usage of the Neo4j graph management functionality.

This script demonstrates how to create Claims and Sentences in the knowledge graph
as would be done by the Claimify pipeline integration.
"""

import sys
import logging
from pathlib import Path
from typing import List

# Setup path for imports  
current_dir = Path(__file__).parent
shared_dir = current_dir.parent.parent  # Go up two levels to get to shared/
sys.path.insert(0, str(shared_dir))

# Import using direct module loading to avoid dependency issues
import importlib.util

def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# Load required modules
config_module = load_module("config", shared_dir / "clarifai_shared" / "config.py")
models_module = load_module("models", current_dir / "models.py") 
neo4j_module = load_module("neo4j_manager", current_dir / "neo4j_manager.py")

ClarifAIConfig = config_module.ClarifAIConfig
ClaimInput = models_module.ClaimInput
SentenceInput = models_module.SentenceInput
Neo4jGraphManager = neo4j_module.Neo4jGraphManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def simulate_claimify_output() -> tuple[List[ClaimInput], List[SentenceInput]]:
    """
    Simulate output from the Claimify pipeline.
    
    Returns:
        Tuple of (claim_inputs, sentence_inputs)
    """
    # Simulate high-quality claims extracted from conversation
    claim_inputs = [
        ClaimInput(
            text="Python is a programming language developed by Guido van Rossum",
            block_id="block_conversation_001_chunk_05",
            entailed_score=0.98,
            coverage_score=0.95,
            decontextualization_score=0.87,
            claim_id="claim_python_language"
        ),
        ClaimInput(
            text="Machine learning algorithms require training data to learn patterns", 
            block_id="block_conversation_001_chunk_12",
            entailed_score=0.92,
            coverage_score=0.88,
            decontextualization_score=0.94,
            claim_id="claim_ml_training_data"
        ),
        ClaimInput(
            text="Neo4j is a graph database that stores data as nodes and relationships",
            block_id="block_conversation_001_chunk_18",
            entailed_score=0.96,
            coverage_score=0.91,
            decontextualization_score=0.89,
            claim_id="claim_neo4j_graph_db"
        ),
        # Example of a claim with some null scores (evaluation agent failure)
        ClaimInput(
            text="The system processes documents efficiently",
            block_id="block_conversation_001_chunk_23",
            entailed_score=0.85,
            coverage_score=None,  # Coverage agent failed
            decontextualization_score=0.76,
            claim_id="claim_system_efficiency"
        )
    ]
    
    # Simulate sentences that didn't produce high-quality claims
    sentence_inputs = [
        SentenceInput(
            text="Hmm, that's really interesting to think about",
            block_id="block_conversation_001_chunk_08",
            ambiguous=True,
            verifiable=False,
            sentence_id="sentence_hmm_interesting"
        ),
        SentenceInput(
            text="What do you think we should do next?",
            block_id="block_conversation_001_chunk_25",
            ambiguous=False,
            verifiable=False,
            sentence_id="sentence_what_do_next"
        ),
        SentenceInput(
            text="This seems complex and has multiple interpretations",
            block_id="block_conversation_001_chunk_30", 
            ambiguous=True,
            verifiable=True,
            sentence_id="sentence_complex_interpretations"
        )
    ]
    
    return claim_inputs, sentence_inputs


def demonstrate_graph_operations():
    """Demonstrate creating and querying graph nodes."""
    
    logger.info("Starting Neo4j graph operations demonstration")
    
    try:
        # Create configuration (this will use defaults if no .env file)
        config = ClarifAIConfig.from_env()
        logger.info(f"Connecting to Neo4j at {config.neo4j.get_neo4j_bolt_url()}")
        
        # Create graph manager with context management
        with Neo4jGraphManager(config) as graph:
            logger.info("Connected to Neo4j successfully")
            
            # Setup schema
            logger.info("Setting up Neo4j schema...")
            graph.setup_schema()
            logger.info("Schema setup completed")
            
            # Get simulated Claimify output
            claim_inputs, sentence_inputs = simulate_claimify_output()
            logger.info(f"Processing {len(claim_inputs)} claims and {len(sentence_inputs)} sentences")
            
            # Create claims in batch
            logger.info("Creating Claim nodes...")
            claims = graph.create_claims(claim_inputs)
            logger.info(f"Successfully created {len(claims)} Claim nodes")
            
            # Create sentences in batch
            logger.info("Creating Sentence nodes...")
            sentences = graph.create_sentences(sentence_inputs)
            logger.info(f"Successfully created {len(sentences)} Sentence nodes")
            
            # Demonstrate retrieval
            logger.info("\nDemonstrating node retrieval:")
            
            # Get a specific claim
            claim_data = graph.get_claim_by_id("claim_python_language")
            if claim_data:
                logger.info(f"Retrieved claim: '{claim_data['text']}'")
                logger.info(f"  Entailed score: {claim_data['entailed_score']}")
                logger.info(f"  Coverage score: {claim_data['coverage_score']}")
                logger.info(f"  Decontextualization score: {claim_data['decontextualization_score']}")
            
            # Get a specific sentence
            sentence_data = graph.get_sentence_by_id("sentence_hmm_interesting")
            if sentence_data:
                logger.info(f"Retrieved sentence: '{sentence_data['text']}'")
                logger.info(f"  Ambiguous: {sentence_data['ambiguous']}")
                logger.info(f"  Verifiable: {sentence_data['verifiable']}")
            
            # Get overall statistics
            counts = graph.count_nodes()
            logger.info("\nGraph statistics:")
            logger.info(f"  Claims: {counts['claims']}")
            logger.info(f"  Sentences: {counts['sentences']}")
            logger.info(f"  Blocks: {counts['blocks']}")
            
        logger.info("Demonstration completed successfully")
        
    except Exception as e:
        logger.error(f"Error during demonstration: {e}")
        raise


def main():
    """Main function to run the demonstration."""
    
    print("Neo4j Graph Management Demonstration")
    print("=====================================")
    print()
    print("This example demonstrates creating Claim and Sentence nodes")
    print("in Neo4j as would be done by the Claimify pipeline integration.")
    print()
    
    # Check if this is just a dry run
    if len(sys.argv) > 1 and sys.argv[1] == "--dry-run":
        print("DRY RUN MODE: Simulating data creation without database connection")
        claim_inputs, sentence_inputs = simulate_claimify_output()
        
        print(f"\nWould create {len(claim_inputs)} claims:")
        for i, claim in enumerate(claim_inputs, 1):
            print(f"  {i}. {claim.text[:50]}...")
            print(f"     Scores: entailed={claim.entailed_score}, coverage={claim.coverage_score}, decontex={claim.decontextualization_score}")
        
        print(f"\nWould create {len(sentence_inputs)} sentences:")
        for i, sentence in enumerate(sentence_inputs, 1):
            print(f"  {i}. {sentence.text[:50]}...")
            print(f"     Properties: ambiguous={sentence.ambiguous}, verifiable={sentence.verifiable}")
        
        print("\nDry run completed. Use without --dry-run to actually connect to Neo4j.")
        return
    
    print("Attempting to connect to Neo4j...")
    print("(Make sure Neo4j is running and environment variables are set)")
    print()
    
    try:
        demonstrate_graph_operations()
        print("\n✅ Demonstration completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Ensure Neo4j is running")
        print("2. Check NEO4J_HOST, NEO4J_USER, NEO4J_PASSWORD environment variables")
        print("3. Verify network connectivity to Neo4j server")
        print("4. Run with --dry-run to test without database connection")
        sys.exit(1)


if __name__ == "__main__":
    main()
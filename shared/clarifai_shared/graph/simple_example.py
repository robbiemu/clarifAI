#!/usr/bin/env python3
"""
Simple standalone example for Neo4j graph functionality.

This demonstrates the core data models without complex imports.
"""

import sys
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Optional
import uuid

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import the models directly
sys.path.insert(0, str(Path(__file__).parent.parent))

import importlib.util

def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

models = load_module("models", Path(__file__).parent / "models.py")

ClaimInput = models.ClaimInput
SentenceInput = models.SentenceInput
Claim = models.Claim
Sentence = models.Sentence


def demonstrate_data_models():
    """Demonstrate the data models functionality."""
    
    print("Data Models Demonstration")
    print("=========================")
    print()
    
    # Create sample claim inputs
    print("1. Creating ClaimInput objects...")
    claim_inputs = [
        ClaimInput(
            text="Python is a programming language developed by Guido van Rossum",
            block_id="block_conversation_001_chunk_05",
            entailed_score=0.98,
            coverage_score=0.95,
            decontextualization_score=0.87
        ),
        ClaimInput(
            text="Machine learning algorithms require training data",
            block_id="block_conversation_001_chunk_12",
            entailed_score=0.92,
            coverage_score=None,  # Simulate agent failure
            decontextualization_score=0.94
        )
    ]
    
    for i, claim_input in enumerate(claim_inputs, 1):
        print(f"   Claim {i}: {claim_input.text[:50]}...")
        print(f"             ID: {claim_input.claim_id}")
        print(f"             Block: {claim_input.block_id}")
        print(f"             Scores: E={claim_input.entailed_score}, C={claim_input.coverage_score}, D={claim_input.decontextualization_score}")
        print()
    
    # Create Claim objects
    print("2. Converting to Claim objects...")
    claims = [Claim.from_input(claim_input) for claim_input in claim_inputs]
    
    for i, claim in enumerate(claims, 1):
        print(f"   Claim {i}: {claim.text[:50]}...")
        print(f"             ID: {claim.claim_id}")
        print(f"             Version: {claim.version}")
        print(f"             Timestamp: {claim.timestamp}")
        print(f"             Dict format: {list(claim.to_dict().keys())}")
        print()
    
    # Create sample sentence inputs
    print("3. Creating SentenceInput objects...")
    sentence_inputs = [
        SentenceInput(
            text="Hmm, that's really interesting",
            block_id="block_conversation_001_chunk_08",
            ambiguous=True,
            verifiable=False
        ),
        SentenceInput(
            text="What should we do next?",
            block_id="block_conversation_001_chunk_25",
            ambiguous=False,
            verifiable=False
        )
    ]
    
    for i, sentence_input in enumerate(sentence_inputs, 1):
        print(f"   Sentence {i}: {sentence_input.text}")
        print(f"               ID: {sentence_input.sentence_id}")
        print(f"               Block: {sentence_input.block_id}")
        print(f"               Properties: ambiguous={sentence_input.ambiguous}, verifiable={sentence_input.verifiable}")
        print()
    
    # Create Sentence objects
    print("4. Converting to Sentence objects...")
    sentences = [Sentence.from_input(sentence_input) for sentence_input in sentence_inputs]
    
    for i, sentence in enumerate(sentences, 1):
        print(f"   Sentence {i}: {sentence.text}")
        print(f"               ID: {sentence.sentence_id}")
        print(f"               Version: {sentence.version}")
        print(f"               Timestamp: {sentence.timestamp}")
        print(f"               Dict format: {list(sentence.to_dict().keys())}")
        print()
    
    # Demonstrate serialization
    print("5. Serialization example...")
    claim_dict = claims[0].to_dict()
    sentence_dict = sentences[0].to_dict()
    
    print("   Claim as dict:")
    for key, value in claim_dict.items():
        print(f"     {key}: {value}")
    print()
    
    print("   Sentence as dict:")
    for key, value in sentence_dict.items():
        print(f"     {key}: {value}")
    print()
    
    print("6. Summary:")
    print(f"   Created {len(claims)} Claims and {len(sentences)} Sentences")
    print(f"   All objects have unique IDs and proper metadata")
    print(f"   Ready for batch insertion into Neo4j database")
    print()


def simulate_claimify_integration():
    """Simulate how this would be used in Claimify integration."""
    
    print("Claimify Integration Simulation")
    print("===============================")
    print()
    
    # Simulate raw Claimify output
    raw_claimify_results = [
        {
            "text": "The Earth orbits the Sun in an elliptical path",
            "source_block": "block_astro_conv_chunk_7",
            "evaluation_scores": {
                "entailed": 0.97,
                "coverage": 0.94,
                "decontextualization": 0.91
            }
        },
        {
            "text": "Neural networks learn through backpropagation",
            "source_block": "block_ml_conv_chunk_15",
            "evaluation_scores": {
                "entailed": 0.89,
                "coverage": 0.85,
                "decontextualization": 0.88
            }
        },
        {
            "text": "This system is efficient", 
            "source_block": "block_sys_conv_chunk_22",
            "evaluation_scores": {
                "entailed": 0.82,
                "coverage": None,  # Coverage agent failed
                "decontextualization": 0.45  # Low score
            }
        }
    ]
    
    # Simulate raw sentences that didn't become claims
    raw_sentence_results = [
        {
            "text": "Wow, I never thought about it that way",
            "source_block": "block_astro_conv_chunk_9",
            "analysis": {"ambiguous": True, "verifiable": False}
        },
        {
            "text": "Can you explain that again?",
            "source_block": "block_ml_conv_chunk_18", 
            "analysis": {"ambiguous": False, "verifiable": False}
        }
    ]
    
    print("1. Processing Claimify results...")
    
    # Convert to ClaimInput objects
    claim_inputs = []
    filtered_claims = []
    
    for result in raw_claimify_results:
        scores = result["evaluation_scores"]
        
        claim_input = ClaimInput(
            text=result["text"],
            block_id=result["source_block"],
            entailed_score=scores.get("entailed"),
            coverage_score=scores.get("coverage"),
            decontextualization_score=scores.get("decontextualization")
        )
        
        # Apply quality filtering (like would be done in real system)
        if claim_input.entailed_score and claim_input.entailed_score >= 0.85:
            if claim_input.decontextualization_score and claim_input.decontextualization_score >= 0.70:
                claim_inputs.append(claim_input)
                print(f"   ✓ High-quality claim: {claim_input.text[:40]}...")
            else:
                filtered_claims.append((claim_input, "Low decontextualization score"))
                print(f"   ✗ Filtered claim: {claim_input.text[:40]}... (low decontextualization)")
        else:
            filtered_claims.append((claim_input, "Low entailment score"))
            print(f"   ✗ Filtered claim: {claim_input.text[:40]}... (low entailment)")
    
    print()
    
    # Convert to SentenceInput objects
    sentence_inputs = []
    for result in raw_sentence_results:
        analysis = result["analysis"]
        
        sentence_input = SentenceInput(
            text=result["text"],
            block_id=result["source_block"],
            ambiguous=analysis.get("ambiguous"),
            verifiable=analysis.get("verifiable")
        )
        sentence_inputs.append(sentence_input)
        print(f"   ➤ Sentence: {sentence_input.text}")
    
    print()
    print("2. Summary of processing:")
    print(f"   High-quality claims: {len(claim_inputs)}")
    print(f"   Filtered claims: {len(filtered_claims)}")
    print(f"   Sentences: {len(sentence_inputs)}")
    print()
    
    print("3. Ready for database insertion:")
    print(f"   Would create {len(claim_inputs)} Claim nodes in Neo4j")
    print(f"   Would create {len(sentence_inputs)} Sentence nodes in Neo4j")
    print(f"   All nodes would have ORIGINATES_FROM relationships to their Block nodes")
    print()
    
    return claim_inputs, sentence_inputs


def main():
    """Main demonstration function."""
    
    print("Neo4j Graph Data Models Demonstration")
    print("====================================")
    print()
    print("This example shows the data models for Claims and Sentences")
    print("without requiring a Neo4j database connection.")
    print()
    
    try:
        # Demonstrate basic data models
        demonstrate_data_models()
        
        print("\n" + "="*50 + "\n")
        
        # Demonstrate Claimify integration
        claim_inputs, sentence_inputs = simulate_claimify_integration()
        
        print("✅ Demonstration completed successfully!")
        print()
        print("Next steps:")
        print("1. Set up Neo4j database with proper credentials")
        print("2. Use Neo4jGraphManager to create these nodes in the database")
        print("3. The manager will handle schema creation, batching, and relationships")
        
    except Exception as e:
        print(f"❌ Error during demonstration: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
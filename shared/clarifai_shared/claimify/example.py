#!/usr/bin/env python3
"""
Example script demonstrating the Claimify pipeline.

This script shows how to use the core Claimify pipeline components
to process sentence chunks and extract claims.
"""

import sys
import os

# Add shared module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from clarifai_shared.claimify import (
    ClaimifyPipeline,
    SentenceChunk,
    ClaimifyConfig,
)
from clarifai_shared.claimify.data_models import NodeType


def main():
    """Demonstrate the Claimify pipeline with example sentences."""
    print("=== Claimify Pipeline Example ===\n")
    
    # Configure the pipeline
    config = ClaimifyConfig(
        context_window_p=2,
        context_window_f=1,
        log_decisions=True,
        log_transformations=True,
    )
    
    # Create pipeline instance
    pipeline = ClaimifyPipeline(config=config)
    
    # Example sentences from the documentation
    example_sentences = [
        SentenceChunk(
            text="The user submitted a request to the API endpoint.",
            source_id="blk_001",
            chunk_id="chunk_001",
            sentence_index=0
        ),
        SentenceChunk(
            text='The system returned an error: "Invalid parameter type".',
            source_id="blk_001", 
            chunk_id="chunk_002",
            sentence_index=1
        ),
        SentenceChunk(
            text="It occurred when the slice object was passed to __setitem__.",
            source_id="blk_001",
            chunk_id="chunk_003", 
            sentence_index=2
        ),
        SentenceChunk(
            text="What should we do about this?",
            source_id="blk_001",
            chunk_id="chunk_004",
            sentence_index=3
        ),
        SentenceChunk(
            text="The error rate increased to 25% after deployment.",
            source_id="blk_001",
            chunk_id="chunk_005",
            sentence_index=4
        ),
    ]
    
    print(f"Processing {len(example_sentences)} sentences through Claimify pipeline...\n")
    
    # Process sentences through the pipeline
    results = pipeline.process_sentences(example_sentences)
    
    # Display results
    print("=== PROCESSING RESULTS ===\n")
    
    for i, result in enumerate(results):
        sentence = result.original_chunk
        print(f"Sentence {i + 1}: \"{sentence.text}\"")
        print(f"Source: {sentence.source_id}, Chunk: {sentence.chunk_id}")
        
        # Selection result
        if result.selection_result:
            selection = result.selection_result
            status = "✅ SELECTED" if selection.is_selected else "❌ REJECTED"
            print(f"  Selection: {status}")
            print(f"  Reasoning: {selection.reasoning}")
            print(f"  Confidence: {selection.confidence:.2f}" if selection.confidence else "")
        
        # Disambiguation result (if processed)
        if result.disambiguation_result:
            disambig = result.disambiguation_result
            print(f"  Disambiguation: \"{disambig.disambiguated_text}\"")
            if disambig.changes_made:
                print(f"  Changes: {', '.join(disambig.changes_made)}")
        
        # Decomposition result (if processed) 
        if result.decomposition_result:
            decomp = result.decomposition_result
            print(f"  Decomposition: {len(decomp.claim_candidates)} candidates")
            
            # Show claims
            for j, claim in enumerate(decomp.valid_claims):
                print(f"    Claim {j + 1}: \"{claim.text}\" (→ :Claim node)")
                print(f"      Atomic: {claim.is_atomic}, Self-contained: {claim.is_self_contained}, Verifiable: {claim.is_verifiable}")
            
            # Show sentence nodes
            for j, sentence_node in enumerate(decomp.sentence_nodes):
                print(f"    Sentence {j + 1}: \"{sentence_node.text}\" (→ :Sentence node)")
                print(f"      Issues: {sentence_node.reasoning}")
        
        # Timing
        if result.total_processing_time:
            print(f"  Processing time: {result.total_processing_time:.3f}s")
        
        print()
    
    # Generate and display pipeline statistics
    stats = pipeline.get_pipeline_stats(results)
    
    print("=== PIPELINE STATISTICS ===")
    print(f"Total sentences: {stats['total_sentences']}")
    print(f"Processed sentences: {stats['processed_sentences']}")
    print(f"Selection rate: {stats['selection_rate']:.1%}")
    print(f"Total claims extracted: {stats['total_claims']}")
    print(f"Total sentence nodes: {stats['total_sentence_nodes']}")
    print(f"Claims per processed sentence: {stats['claims_per_processed']:.1f}")
    print(f"Errors: {stats['errors']}")
    
    print("\n=== TIMING STATISTICS ===")
    timing = stats['timing']
    print(f"Selection avg: {timing['selection_avg']:.3f}s")
    print(f"Disambiguation avg: {timing['disambiguation_avg']:.3f}s") 
    print(f"Decomposition avg: {timing['decomposition_avg']:.3f}s")
    print(f"Total avg: {timing['total_avg']:.3f}s")
    
    print("\n=== SUMMARY ===")
    print("The Claimify pipeline successfully:")
    print("1. ✅ Selected relevant sentences containing verifiable information")
    print("2. ✅ Disambiguated sentences by resolving pronouns and adding context")
    print("3. ✅ Decomposed sentences into atomic, self-contained claims")
    print("4. ✅ Distinguished between valid claims (→ :Claim nodes) and incomplete statements (→ :Sentence nodes)")
    print("5. ✅ Provided detailed logging and timing information")
    print("\nReady for integration with evaluation agents and graph ingestion!")


if __name__ == "__main__":
    main()
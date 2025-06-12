"""
Complete integration example for Claimify pipeline with Neo4j persistence.

This example demonstrates the end-to-end workflow from sentence processing
through the Claimify pipeline to Neo4j graph persistence, as required for
Sprint 3 functionality.
"""

import sys
import os
import logging
from typing import List

# Add the shared directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from clarifai_shared.claimify import (
    ClaimifyPipeline,
    ClaimifyConfig,
    SentenceChunk,
    ClaimifyGraphIntegration,
    create_graph_manager_from_config,
)
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_complete_claimify_workflow():
    """
    Demonstrate the complete Claimify workflow with Neo4j integration.
    
    This example shows how to:
    1. Configure the Claimify pipeline
    2. Process sentences through Selection → Disambiguation → Decomposition
    3. Persist results to Neo4j as (:Claim) and (:Sentence) nodes
    """
    
    logger.info("[example.run_complete_claimify_workflow] Starting complete Claimify workflow demonstration")
    
    # Step 1: Load configuration
    try:
        config_path = "/home/runner/work/clarifAI/clarifAI/settings/clarifai.config.yaml"
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        logger.info("[example.run_complete_claimify_workflow] Configuration loaded successfully")
    except Exception as e:
        logger.warning(f"[example.run_complete_claimify_workflow] Failed to load config: {e}")
        # Use default configuration
        config = {
            'databases': {
                'neo4j': {
                    'host': 'neo4j',
                    'port': 7687
                }
            }
        }
    
    # Step 2: Initialize Claimify pipeline
    claimify_config = ClaimifyConfig(
        context_window_p=3,
        context_window_f=1,
        default_model="gpt-3.5-turbo",
        max_retries=3,
        timeout_seconds=30,
        temperature=0.1,
        log_decisions=True,
        log_transformations=True,
        log_timing=True
    )
    
    pipeline = ClaimifyPipeline(config=claimify_config)
    logger.info("[example.run_complete_claimify_workflow] Claimify pipeline initialized")
    
    # Step 3: Initialize Neo4j graph manager and integration
    graph_manager = create_graph_manager_from_config(config)
    integration = ClaimifyGraphIntegration(graph_manager)
    logger.info("[example.run_complete_claimify_workflow] Neo4j integration initialized")
    
    # Step 4: Prepare test sentences (examples from on-claim_generation.md)
    test_sentences = [
        # Verifiable technical content (should become claims)
        SentenceChunk(
            text="The system reported an error with code 500 during the morning deployment.",
            source_id="blk_conv_001",
            chunk_id="chunk_001",
            sentence_index=0
        ),
        SentenceChunk(
            text="The database connection failed at 10:30 AM on March 15th.",
            source_id="blk_conv_001",
            chunk_id="chunk_002",
            sentence_index=1
        ),
        SentenceChunk(
            text="User authentication service became unavailable for 25 minutes.",
            source_id="blk_conv_001",
            chunk_id="chunk_003",
            sentence_index=2
        ),
        
        # Questions and ambiguous content (should become sentences)
        SentenceChunk(
            text="What should we do about this issue?",
            source_id="blk_conv_002",
            chunk_id="chunk_004",
            sentence_index=0
        ),
        SentenceChunk(
            text="It failed again.",
            source_id="blk_conv_002",
            chunk_id="chunk_005",
            sentence_index=1
        ),
        SentenceChunk(
            text="Hmm.",
            source_id="blk_conv_002",
            chunk_id="chunk_006",
            sentence_index=2
        ),
        
        # Mixed content with potential decomposition
        SentenceChunk(
            text="The API responded with timeout errors and the cache was cleared automatically.",
            source_id="blk_conv_003",
            chunk_id="chunk_007",
            sentence_index=0
        ),
    ]
    
    logger.info(f"[example.run_complete_claimify_workflow] Processing {len(test_sentences)} sentence chunks")
    
    # Step 5: Process sentences through Claimify pipeline
    results = pipeline.process_sentences(test_sentences)
    
    # Step 6: Generate and display pipeline statistics
    stats = pipeline.get_pipeline_stats(results)
    logger.info("[example.run_complete_claimify_workflow] Pipeline processing completed")
    logger.info(f"[example.run_complete_claimify_workflow] Pipeline statistics:")
    logger.info(f"  - Total sentences: {stats['total_sentences']}")
    logger.info(f"  - Selection rate: {stats['selection_rate']:.1%}")
    logger.info(f"  - Total claims extracted: {stats['total_claims']}")
    logger.info(f"  - Total sentence nodes: {stats['total_sentence_nodes']}")
    logger.info(f"  - Processing time: {stats['timing']['total_avg']:.3f}s")
    
    # Step 7: Persist results to Neo4j
    logger.info("[example.run_complete_claimify_workflow] Persisting results to Neo4j")
    claims_created, sentences_created, errors = integration.persist_claimify_results(results)
    
    logger.info(f"[example.run_complete_claimify_workflow] Persistence completed:")
    logger.info(f"  - Claims created: {claims_created}")
    logger.info(f"  - Sentences created: {sentences_created}")
    logger.info(f"  - Errors: {len(errors)}")
    
    if errors:
        logger.warning("[example.run_complete_claimify_workflow] Persistence errors encountered:")
        for error in errors:
            logger.warning(f"  - {error}")
    
    # Step 8: Display detailed results
    display_detailed_results(results)
    
    logger.info("[example.run_complete_claimify_workflow] Workflow completed successfully")
    
    return {
        'pipeline_stats': stats,
        'claims_created': claims_created,
        'sentences_created': sentences_created,
        'errors': errors,
        'results': results
    }


def display_detailed_results(results: List):
    """Display detailed processing results for each sentence."""
    logger.info("[example.display_detailed_results] Detailed processing results:")
    
    for i, result in enumerate(results, 1):
        logger.info(f"\n--- Sentence {i} ---")
        logger.info(f"Original: '{result.original_chunk.text}'")
        logger.info(f"Source ID: {result.original_chunk.source_id}")
        
        if result.selection_result:
            selected = "✅ SELECTED" if result.selection_result.is_selected else "❌ REJECTED"
            logger.info(f"Selection: {selected}")
            
            if result.selection_result.reasoning:
                logger.info(f"  Reasoning: {result.selection_result.reasoning}")
        
        if result.disambiguation_result:
            logger.info(f"Disambiguation: '{result.disambiguation_result.disambiguated_text}'")
            if result.disambiguation_result.changes_made:
                logger.info(f"  Changes: {', '.join(result.disambiguation_result.changes_made)}")
        
        if result.decomposition_result:
            valid_claims = result.decomposition_result.valid_claims
            sentence_nodes = result.decomposition_result.sentence_nodes
            
            logger.info(f"Decomposition: {len(valid_claims)} claims, {len(sentence_nodes)} sentence nodes")
            
            for j, claim in enumerate(valid_claims, 1):
                logger.info(f"  Claim {j}: '{claim.text}'")
                criteria = []
                if claim.is_atomic:
                    criteria.append("atomic")
                if claim.is_self_contained:
                    criteria.append("self-contained")
                if claim.is_verifiable:
                    criteria.append("verifiable")
                logger.info(f"    Criteria: {', '.join(criteria)}")
            
            for j, sentence_node in enumerate(sentence_nodes, 1):
                logger.info(f"  Sentence {j}: '{sentence_node.text}'")
                issues = []
                if not sentence_node.is_atomic:
                    issues.append("not atomic")
                if not sentence_node.is_self_contained:
                    issues.append("not self-contained")
                if not sentence_node.is_verifiable:
                    issues.append("not verifiable")
                logger.info(f"    Issues: {', '.join(issues)}")
        
        # Show final graph node types
        final_claims = len(result.final_claims)
        final_sentences = len(result.final_sentences)
        
        if final_claims > 0:
            logger.info(f"→ Creates {final_claims} (:Claim) node(s)")
        if final_sentences > 0:
            logger.info(f"→ Creates {final_sentences} (:Sentence) node(s)")
        if final_claims == 0 and final_sentences == 0 and not result.was_processed:
            logger.info("→ Creates 1 (:Sentence) node (rejected by selection)")


def demo_configuration_integration():
    """Demonstrate configuration integration with real config file."""
    logger.info("[example.demo_configuration_integration] Demonstrating configuration integration")
    
    try:
        from clarifai_shared.claimify.config_integration import (
            load_claimify_config_from_file,
            get_model_config_for_stage
        )
        
        # Load configuration from actual config file
        config_path = "/home/runner/work/clarifAI/clarifAI/settings/clarifai.config.yaml"
        claimify_config = load_claimify_config_from_file(config_path)
        
        logger.info(f"[example.demo_configuration_integration] Loaded configuration:")
        logger.info(f"  - Context window: p={claimify_config.context_window_p}, f={claimify_config.context_window_f}")
        logger.info(f"  - Default model: {claimify_config.default_model}")
        logger.info(f"  - Selection model: {claimify_config.get_model_for_stage('selection')}")
        logger.info(f"  - Disambiguation model: {claimify_config.get_model_for_stage('disambiguation')}")
        logger.info(f"  - Decomposition model: {claimify_config.get_model_for_stage('decomposition')}")
        logger.info(f"  - Max retries: {claimify_config.max_retries}")
        logger.info(f"  - Timeout: {claimify_config.timeout_seconds}s")
        logger.info(f"  - Temperature: {claimify_config.temperature}")
        
        return claimify_config
        
    except Exception as e:
        logger.error(f"[example.demo_configuration_integration] Configuration demo failed: {e}")
        return None


if __name__ == "__main__":
    """Run the complete integration example."""
    print("🚀 ClarifAI Claimify Pipeline + Neo4j Integration Example")
    print("=" * 60)
    
    # Demo configuration integration
    config = demo_configuration_integration()
    if config:
        print("✅ Configuration integration working")
    else:
        print("⚠️  Using default configuration")
    
    print("\n" + "=" * 60)
    
    # Run complete workflow
    try:
        workflow_results = run_complete_claimify_workflow()
        
        print("\n" + "=" * 60)
        print("🎉 WORKFLOW COMPLETED SUCCESSFULLY")
        print("=" * 60)
        print(f"📊 Pipeline processed {workflow_results['pipeline_stats']['total_sentences']} sentences")
        print(f"🎯 Selection rate: {workflow_results['pipeline_stats']['selection_rate']:.1%}")
        print(f"📝 Claims created: {workflow_results['claims_created']}")
        print(f"📄 Sentences created: {workflow_results['sentences_created']}")
        print(f"⚡ Processing time: {workflow_results['pipeline_stats']['timing']['total_avg']:.3f}s")
        
        if workflow_results['errors']:
            print(f"⚠️  Errors encountered: {len(workflow_results['errors'])}")
        else:
            print("✅ No errors encountered")
            
    except Exception as e:
        print(f"\n❌ WORKFLOW FAILED: {e}")
        import traceback
        traceback.print_exc()
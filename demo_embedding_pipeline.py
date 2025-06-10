#!/usr/bin/env python3
"""
ClarifAI Embedding System Demo

This script demonstrates the complete embedding pipeline functionality
including chunking, embedding generation, and vector storage.

Usage:
    python demo_embedding_pipeline.py [--config CONFIG_FILE] [--mock-db]

Options:
    --config CONFIG_FILE    Path to configuration file (default: clarifai.config.yaml)
    --mock-db              Use mock database for testing (no actual database required)
    --verbose              Enable verbose logging
    --test-similarity      Run similarity search tests
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Any, Dict

# Add the shared module to the path for local testing
sys.path.insert(0, str(Path(__file__).parent / "shared"))

try:
    from clarifai_shared.config import load_config
    from clarifai_shared.embedding import EmbeddingPipeline
except ImportError as e:
    print(f"Error importing ClarifAI modules: {e}")
    print(
        "Make sure you're running this from the repository root and dependencies are installed."
    )
    sys.exit(1)


def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )


def create_sample_tier1_content() -> str:
    """Create sample Tier 1 Markdown content for testing."""
    return """
<!-- clarifai:title=Demo Conversation -->
<!-- clarifai:created_at=2024-01-15T10:00:00Z -->
<!-- clarifai:participants=["Alice", "Bob", "Charlie"] -->
<!-- clarifai:message_count=4 -->
<!-- clarifai:plugin_metadata={} -->

Alice: Hello everyone! I wanted to discuss our upcoming project on natural language processing.
<!-- clarifai:id=blk_demo01 ver=1 -->
^blk_demo01

Bob: That sounds great, Alice. I've been reading about transformer models and their applications in text understanding.
<!-- clarifai:id=blk_demo02 ver=1 -->
^blk_demo02

Charlie: I'm particularly interested in how we can use embeddings to find similar content across our document collection.
<!-- clarifai:id=blk_demo03 ver=1 -->
^blk_demo03

Alice: Excellent point, Charlie. We could implement a system that chunks documents, creates embeddings, and stores them in a vector database for efficient similarity search. This would be similar to what modern RAG systems do.
<!-- clarifai:id=blk_demo04 ver=1 -->
^blk_demo04
"""


def mock_database_components():
    """Create mock database components for testing without actual database."""
    from unittest.mock import Mock

    from clarifai_shared.embedding.storage import VectorStoreMetrics

    # Mock the vector store
    mock_store = Mock()
    mock_store.store_embeddings.return_value = VectorStoreMetrics(
        total_vectors=4, successful_inserts=4, failed_inserts=0
    )
    mock_store.get_store_metrics.return_value = VectorStoreMetrics(
        total_vectors=4, successful_inserts=4, failed_inserts=0
    )
    mock_store.similarity_search.return_value = [
        (
            {
                "clarifai_block_id": "blk_demo01",
                "chunk_index": 0,
                "text": "Sample text 1",
            },
            0.95,
        ),
        (
            {
                "clarifai_block_id": "blk_demo02",
                "chunk_index": 0,
                "text": "Sample text 2",
            },
            0.87,
        ),
    ]

    return mock_store


def run_chunking_demo(
    pipeline: EmbeddingPipeline, tier1_content: str
) -> Dict[str, Any]:
    """Demonstrate the chunking functionality."""
    print("\n" + "=" * 50)
    print("CHUNKING DEMONSTRATION")
    print("=" * 50)

    chunks = pipeline.chunker.chunk_tier1_blocks(tier1_content)

    print(f"Input Tier 1 content length: {len(tier1_content)} characters")
    print(f"Generated chunks: {len(chunks)}")
    print()

    for i, chunk in enumerate(chunks):
        print(f"Chunk {i + 1}:")
        print(f"  Block ID: {chunk.clarifai_block_id}")
        print(f"  Chunk Index: {chunk.chunk_index}")
        print(f"  Text: {chunk.text[:100]}{'...' if len(chunk.text) > 100 else ''}")
        print(f"  Length: {len(chunk.text)} characters")
        print()

    return {"total_chunks": len(chunks), "chunks": chunks}


def run_embedding_demo(
    pipeline: EmbeddingPipeline, chunks: list, mock_db: bool = False
) -> Dict[str, Any]:
    """Demonstrate the embedding generation."""
    print("\n" + "=" * 50)
    print("EMBEDDING GENERATION DEMONSTRATION")
    print("=" * 50)

    if not chunks:
        print("No chunks to embed!")
        return {"embedded_chunks": 0}

    print(
        f"Embedding {len(chunks)} chunks using model: {pipeline.embedding_generator.model_name}"
    )

    # Take first few chunks for demo to avoid long processing times
    demo_chunks = chunks[:3] if len(chunks) > 3 else chunks

    try:
        embedded_chunks = pipeline.embedding_generator.embed_chunks(demo_chunks)

        print(f"Successfully embedded {len(embedded_chunks)} chunks")

        if embedded_chunks:
            sample_embedding = embedded_chunks[0]
            print(f"Sample embedding dimension: {sample_embedding.embedding_dim}")
            print(f"Sample embedding preview: {sample_embedding.embedding[:5]}...")

            # Validate embeddings
            validation_report = pipeline.embedding_generator.validate_embeddings(
                embedded_chunks
            )
            print(f"Validation status: {validation_report['status']}")
            print(f"All embeddings valid: {validation_report['all_embeddings_valid']}")

        return {
            "embedded_chunks": len(embedded_chunks),
            "embedding_dim": embedded_chunks[0].embedding_dim if embedded_chunks else 0,
            "model_name": pipeline.embedding_generator.model_name,
        }

    except Exception as e:
        print(f"Embedding generation failed: {e}")
        if not mock_db:
            print("This might be due to missing dependencies or model download issues.")
            print(
                "Try running with --mock-db for testing without actual embedding models."
            )
        return {"embedded_chunks": 0, "error": str(e)}


def run_storage_demo(
    pipeline: EmbeddingPipeline, embedded_chunks: list, mock_db: bool = False
) -> Dict[str, Any]:
    """Demonstrate vector storage functionality."""
    print("\n" + "=" * 50)
    print("VECTOR STORAGE DEMONSTRATION")
    print("=" * 50)

    if mock_db:
        print("Using mock database for demonstration...")
        mock_store = mock_database_components()
        pipeline.vector_store = mock_store

        # Simulate storage
        metrics = mock_store.store_embeddings(embedded_chunks)
        print(f"Mock storage complete: {metrics.successful_inserts} chunks stored")

        return {
            "stored_chunks": metrics.successful_inserts,
            "failed_chunks": metrics.failed_inserts,
            "using_mock": True,
        }

    if not embedded_chunks:
        print("No embedded chunks to store!")
        return {"stored_chunks": 0}

    try:
        print(f"Storing {len(embedded_chunks)} embedded chunks in PostgreSQL...")
        print(f"Collection: {pipeline.config.embedding.collection_name}")

        metrics = pipeline.vector_store.store_embeddings(embedded_chunks)

        print("Storage complete:")
        print(f"  Total vectors: {metrics.total_vectors}")
        print(f"  Successful inserts: {metrics.successful_inserts}")
        print(f"  Failed inserts: {metrics.failed_inserts}")

        return {
            "stored_chunks": metrics.successful_inserts,
            "failed_chunks": metrics.failed_inserts,
            "using_mock": False,
        }

    except Exception as e:
        print(f"Vector storage failed: {e}")
        print("This might be due to database connection issues.")
        print(
            "Check your PostgreSQL configuration and ensure pgvector extension is installed."
        )
        return {
            "stored_chunks": 0,
            "failed_chunks": len(embedded_chunks),
            "error": str(e),
        }


def run_similarity_search_demo(pipeline: EmbeddingPipeline):
    """Demonstrate similarity search functionality."""
    print("\n" + "=" * 50)
    print("SIMILARITY SEARCH DEMONSTRATION")
    print("=" * 50)

    test_queries = [
        "natural language processing",
        "transformer models",
        "document similarity",
        "vector database search",
    ]

    for query in test_queries:
        print(f"\nQuery: '{query}'")

        try:
            results = pipeline.search_similar_chunks(
                query_text=query, top_k=3, similarity_threshold=0.7
            )

            if results:
                print(f"Found {len(results)} similar chunks:")
                for i, result in enumerate(results):
                    print(f"  {i + 1}. Block: {result['clarifai_block_id']}")
                    print(f"     Score: {result['similarity_score']:.3f}")
                    print(f"     Text: {result.get('text', 'N/A')[:80]}...")
            else:
                print("  No similar chunks found")

        except Exception as e:
            print(f"  Search failed: {e}")


def run_pipeline_demo(
    pipeline: EmbeddingPipeline, tier1_content: str, mock_db: bool = False
) -> Dict[str, Any]:
    """Demonstrate the complete pipeline."""
    print("\n" + "=" * 50)
    print("COMPLETE PIPELINE DEMONSTRATION")
    print("=" * 50)

    if mock_db:
        # Mock the vector store for complete pipeline test
        pipeline.vector_store = mock_database_components()

    print("Processing Tier 1 content through complete pipeline...")

    try:
        result = pipeline.process_tier1_content(tier1_content)

        print("Pipeline Result:")
        print(f"  Success: {result.success}")
        print(f"  Total chunks: {result.total_chunks}")
        print(f"  Embedded chunks: {result.embedded_chunks}")
        print(f"  Stored chunks: {result.stored_chunks}")
        print(f"  Failed chunks: {result.failed_chunks}")

        if result.errors:
            print(f"  Errors: {result.errors}")

        return {
            "success": result.success,
            "total_chunks": result.total_chunks,
            "stored_chunks": result.stored_chunks,
        }

    except Exception as e:
        print(f"Pipeline failed: {e}")
        return {"success": False, "error": str(e)}


def run_status_demo(pipeline: EmbeddingPipeline):
    """Demonstrate pipeline status checking."""
    print("\n" + "=" * 50)
    print("PIPELINE STATUS DEMONSTRATION")
    print("=" * 50)

    try:
        status = pipeline.get_pipeline_status()

        print(f"Overall Status: {status['overall_status']}")
        print("\nComponent Status:")

        for component, info in status["components"].items():
            print(f"  {component}: {info['status']}")
            if "error" in info:
                print(f"    Error: {info['error']}")
            elif component == "vector_store" and "total_vectors" in info:
                print(f"    Total vectors: {info['total_vectors']}")
            elif component == "embedding_model" and "model_name" in info:
                print(f"    Model: {info['model_name']}")
                print(f"    Dimension: {info.get('embedding_dim', 'N/A')}")

    except Exception as e:
        print(f"Status check failed: {e}")


def main():
    """Main demo function."""
    parser = argparse.ArgumentParser(description="ClarifAI Embedding System Demo")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument(
        "--mock-db", action="store_true", help="Use mock database for testing"
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument(
        "--test-similarity", action="store_true", help="Run similarity search tests"
    )

    args = parser.parse_args()

    setup_logging(args.verbose)

    print("ClarifAI Embedding System Demo")
    print("=" * 50)

    # Load configuration
    try:
        if args.mock_db:
            # Use minimal config for mock testing
            config = None
        else:
            config = load_config(config_file=args.config, validate=False)

        print(f"Configuration loaded: {'Mock mode' if args.mock_db else 'Full mode'}")

    except Exception as e:
        print(f"Configuration loading failed: {e}")
        if not args.mock_db:
            print("Try running with --mock-db for testing without database.")
        return 1

    # Initialize pipeline
    try:
        if args.mock_db:
            # Create minimal pipeline for testing
            from unittest.mock import patch

            with patch("clarifai_shared.embedding.load_config"):
                pipeline = EmbeddingPipeline()
        else:
            pipeline = EmbeddingPipeline(config)

        print("Embedding pipeline initialized successfully")

    except Exception as e:
        print(f"Pipeline initialization failed: {e}")
        return 1

    # Create sample content
    tier1_content = create_sample_tier1_content()

    # Run demonstrations
    demo_results = {}

    # 1. Chunking demo
    chunking_result = run_chunking_demo(pipeline, tier1_content)
    demo_results["chunking"] = chunking_result

    # 2. Embedding demo (only if we have chunks)
    if chunking_result["total_chunks"] > 0:
        embedding_result = run_embedding_demo(
            pipeline, chunking_result["chunks"], args.mock_db
        )
        demo_results["embedding"] = embedding_result

    # 3. Complete pipeline demo
    pipeline_result = run_pipeline_demo(pipeline, tier1_content, args.mock_db)
    demo_results["pipeline"] = pipeline_result

    # 4. Similarity search demo (if requested)
    if args.test_similarity:
        run_similarity_search_demo(pipeline, args.mock_db)

    # 5. Status demo
    if not args.mock_db:
        run_status_demo(pipeline)

    # Summary
    print("\n" + "=" * 50)
    print("DEMO SUMMARY")
    print("=" * 50)

    print(
        f"Chunking: {demo_results.get('chunking', {}).get('total_chunks', 0)} chunks generated"
    )
    print(
        f"Embedding: {demo_results.get('embedding', {}).get('embedded_chunks', 0)} chunks embedded"
    )
    print(
        f"Pipeline: {'Success' if demo_results.get('pipeline', {}).get('success') else 'Failed'}"
    )

    if args.mock_db:
        print("\nNote: This demo used mock components. For full functionality:")
        print("1. Install all dependencies: uv pip install -r requirements.txt")
        print("2. Setup PostgreSQL with pgvector extension")
        print("3. Configure environment variables")
        print("4. Run without --mock-db flag")

    return 0


if __name__ == "__main__":
    sys.exit(main())

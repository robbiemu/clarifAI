"""
Tests for the concept embedding refresh job.

This module tests the functionality of refreshing concept embeddings
from Tier 3 concept files following the specifications in
docs/arch/on-refreshing_concept_embeddings.md
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock

from aclarai_scheduler.concept_refresh import ConceptEmbeddingRefreshJob


class MockVectorStoreForConcepts:
    """Simple mock vector store with upsert method for concept testing."""

    def __init__(self):
        self.upsert = Mock()
        self.delete_chunks_by_block_id = Mock(return_value=0)
        self.store_embeddings = Mock()


class MockVectorStoreMetrics:
    """Mock metrics for vector store operations."""

    def __init__(self, successful_inserts=1, failed_inserts=0):
        self.successful_inserts = successful_inserts
        self.failed_inserts = failed_inserts


def test_extract_semantic_text():
    """Test semantic text extraction from concept file content."""
    # Create mocks for dependencies
    mock_config = MagicMock()
    mock_config.vault_path = "/tmp/test_vault"
    mock_neo4j = Mock()
    mock_embedding_gen = Mock()
    mock_vector_store = MockVectorStoreForConcepts()

    job = ConceptEmbeddingRefreshJob(
        config=mock_config,
        neo4j_manager=mock_neo4j,
        embedding_generator=mock_embedding_gen,
        vector_store=mock_vector_store
    )

    # Test content with metadata and anchors
    file_content = """# Machine Learning

Machine learning is a subset of artificial intelligence.

Key characteristics:
- Pattern recognition
- Automatic improvement

<!-- aclarai:id=concept_machine_learning ver=1 -->
^concept_machine_learning
"""

    expected_semantic_text = """# Machine Learning

Machine learning is a subset of artificial intelligence.

Key characteristics:
- Pattern recognition
- Automatic improvement"""

    result = job._extract_semantic_text(file_content)
    assert result.strip() == expected_semantic_text.strip()


def test_extract_semantic_text_no_metadata():
    """Test semantic text extraction when there's no metadata."""
    mock_config = MagicMock()
    mock_config.vault_path = "/tmp/test_vault"
    mock_neo4j = Mock()
    mock_embedding_gen = Mock()
    mock_vector_store = MockVectorStoreForConcepts()

    job = ConceptEmbeddingRefreshJob(
        config=mock_config,
        neo4j_manager=mock_neo4j,
        embedding_generator=mock_embedding_gen,
        vector_store=mock_vector_store
    )

    file_content = """# Deep Learning

Deep learning uses neural networks with multiple layers."""

    result = job._extract_semantic_text(file_content)
    assert result.strip() == file_content.strip()


def test_compute_hash():
    """Test SHA256 hash computation."""
    mock_config = MagicMock()
    mock_config.vault_path = "/tmp/test_vault"
    mock_neo4j = Mock()
    mock_embedding_gen = Mock()
    mock_vector_store = MockVectorStoreForConcepts()

    job = ConceptEmbeddingRefreshJob(
        config=mock_config,
        neo4j_manager=mock_neo4j,
        embedding_generator=mock_embedding_gen,
        vector_store=mock_vector_store
    )

    text = "Machine learning is awesome"
    hash1 = job._compute_hash(text)
    hash2 = job._compute_hash(text)

    # Same text should produce same hash
    assert hash1 == hash2
    assert len(hash1) == 64  # SHA256 produces 64 character hex string

    # Different text should produce different hash
    different_text = "Deep learning is awesome"
    hash3 = job._compute_hash(different_text)
    assert hash1 != hash3


def test_process_concept_file_no_changes():
    """Test processing a concept file when no changes are detected."""
    # Create temporary vault directory
    with tempfile.TemporaryDirectory() as temp_dir:
        vault_path = Path(temp_dir)
        concepts_path = vault_path / "concepts"
        concepts_path.mkdir()

        # Create test config
        mock_config = MagicMock()
        mock_config.vault_path = str(vault_path)

        # Create mocks for dependencies
        mock_neo4j = Mock()
        mock_embedding_gen = Mock()
        mock_vector_store = MockVectorStoreForConcepts()

        # Create test concept file
        concept_file = concepts_path / "test_concept.md"
        content = """# Test Concept

This is a test concept.

<!-- aclarai:id=concept_test_concept ver=1 -->
^concept_test_concept"""

        with open(concept_file, "w") as f:
            f.write(content)

        job = ConceptEmbeddingRefreshJob(
            config=mock_config,
            neo4j_manager=mock_neo4j,
            embedding_generator=mock_embedding_gen,
            vector_store=mock_vector_store
        )

        # Mock that the stored hash matches current hash
        semantic_text = job._extract_semantic_text(content)
        current_hash = job._compute_hash(semantic_text)
        job._get_stored_embedding_hash = Mock(return_value=current_hash)

        # Process the file
        processed, updated = job._process_concept_file(concept_file)

        assert processed is True
        assert updated is False  # No update needed

        # Verify that embedding was not generated
        mock_embedding_gen.embed_text.assert_not_called()


def test_process_concept_file_with_changes():
    """Test processing a concept file when changes are detected."""
    # Create temporary vault directory
    with tempfile.TemporaryDirectory() as temp_dir:
        vault_path = Path(temp_dir)
        concepts_path = vault_path / "concepts"
        concepts_path.mkdir()

        # Create test config
        mock_config = MagicMock()
        mock_config.vault_path = str(vault_path)

        # Create mocks for dependencies
        mock_neo4j = Mock()
        mock_embedding_gen = Mock()
        mock_embedding_gen.model_name = "test-model"
        mock_vector_store = MockVectorStoreForConcepts()

        # Create test concept file
        concept_file = concepts_path / "test_concept.md"
        content = """# Test Concept

This is a test concept with updated content.

<!-- aclarai:id=concept_test_concept ver=2 -->
^concept_test_concept"""

        with open(concept_file, "w") as f:
            f.write(content)

        job = ConceptEmbeddingRefreshJob(
            config=mock_config,
            neo4j_manager=mock_neo4j,
            embedding_generator=mock_embedding_gen,
            vector_store=mock_vector_store
        )

        # Mock that the stored hash is different (indicating changes)
        job._get_stored_embedding_hash = Mock(return_value="old_hash_value")
        job._update_neo4j_metadata = Mock()

        # Mock embedding generation
        mock_embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        mock_embedding_gen.embed_text.return_value = mock_embedding

        # Process the file
        processed, updated = job._process_concept_file(concept_file)

        assert processed is True
        assert updated is True  # Update was needed

        # Verify that embedding was generated
        mock_embedding_gen.embed_text.assert_called_once()

        # Verify that vector store upsert was called (for mocks with upsert method)
        mock_vector_store.upsert.assert_called_once_with("test_concept", mock_embedding)

        # Verify Neo4j update was called
        job._update_neo4j_metadata.assert_called_once()


def test_run_job_no_concepts_directory():
    """Test run_job when concepts directory doesn't exist."""
    # Create test config with non-existent concepts directory
    mock_config = MagicMock()
    mock_config.vault_path = "/nonexistent/vault"

    # Create mocks for dependencies
    mock_neo4j = Mock()
    mock_embedding_gen = Mock()
    mock_vector_store = MockVectorStoreForConcepts()

    job = ConceptEmbeddingRefreshJob(
        config=mock_config,
        neo4j_manager=mock_neo4j,
        embedding_generator=mock_embedding_gen,
        vector_store=mock_vector_store
    )

    result = job.run_job()

    assert result["success"] is False
    assert result["concepts_processed"] == 0
    assert result["concepts_updated"] == 0
    assert "Concepts directory does not exist" in result["error_details"]


def test_run_job_with_concept_files():
    """Test run_job with actual concept files."""
    # Create temporary vault directory
    with tempfile.TemporaryDirectory() as temp_dir:
        vault_path = Path(temp_dir)
        concepts_path = vault_path / "concepts"
        concepts_path.mkdir()

        # Create test config
        mock_config = MagicMock()
        mock_config.vault_path = str(vault_path)

        # Create mocks for dependencies
        mock_neo4j = Mock()
        mock_embedding_gen = Mock()
        mock_vector_store = MockVectorStoreForConcepts()

        # Create multiple test concept files
        concepts = [
            ("concept1.md", "# Concept 1\n\nFirst concept content."),
            ("concept2.md", "# Concept 2\n\nSecond concept content."),
        ]

        for filename, content in concepts:
            with open(concepts_path / filename, "w") as f:
                f.write(content)

        job = ConceptEmbeddingRefreshJob(
            config=mock_config,
            neo4j_manager=mock_neo4j,
            embedding_generator=mock_embedding_gen,
            vector_store=mock_vector_store
        )

        # Mock the process_concept_file method
        job._process_concept_file = Mock(return_value=(True, True))

        result = job.run_job()

        assert result["success"] is True
        assert result["concepts_processed"] == 2
        assert result["concepts_updated"] == 2
        assert result["concepts_skipped"] == 0
        assert result["errors"] == 0


def test_get_stored_embedding_hash_not_found():
    """Test getting stored embedding hash when concept doesn't exist."""
    mock_config = MagicMock()
    mock_config.vault_path = "/tmp/test_vault"

    # Mock Neo4j manager session
    mock_session = MagicMock()
    mock_result = MagicMock()
    mock_result.single.return_value = None
    mock_session.run.return_value = mock_result

    mock_neo4j_manager = MagicMock()
    mock_neo4j_manager.session.return_value.__enter__.return_value = mock_session

    # Create mocks for other dependencies
    mock_embedding_gen = Mock()
    mock_vector_store = MockVectorStoreForConcepts()

    job = ConceptEmbeddingRefreshJob(
        config=mock_config,
        neo4j_manager=mock_neo4j_manager,
        embedding_generator=mock_embedding_gen,
        vector_store=mock_vector_store
    )

    result = job._get_stored_embedding_hash("nonexistent_concept")

    assert result is None


def test_get_stored_embedding_hash_found():
    """Test getting stored embedding hash when concept exists."""
    mock_config = MagicMock()
    mock_config.vault_path = "/tmp/test_vault"

    # Mock Neo4j manager session
    mock_session = MagicMock()
    mock_result = MagicMock()
    mock_record = {"hash": "stored_hash_value"}
    mock_result.single.return_value = mock_record
    mock_session.run.return_value = mock_result

    mock_neo4j_manager = MagicMock()
    mock_neo4j_manager.session.return_value.__enter__.return_value = mock_session

    # Create mocks for other dependencies
    mock_embedding_gen = Mock()
    mock_vector_store = MockVectorStoreForConcepts()

    job = ConceptEmbeddingRefreshJob(
        config=mock_config,
        neo4j_manager=mock_neo4j_manager,
        embedding_generator=mock_embedding_gen,
        vector_store=mock_vector_store
    )

    result = job._get_stored_embedding_hash("existing_concept")

    assert result == "stored_hash_value"


def test_update_vector_store_with_real_store():
    """Test the _update_vector_store method with a real vector store (no upsert method)."""
    mock_config = MagicMock()
    mock_config.vault_path = "/tmp/test_vault"

    # Create mocks for dependencies
    mock_neo4j = Mock()
    mock_embedding_gen = Mock()
    mock_embedding_gen.model_name = "test-model"

    # Create a mock vector store without upsert method (like the real one)
    mock_vector_store = Mock()
    mock_vector_store.delete_chunks_by_block_id.return_value = 2  # Simulate deleting 2 old chunks
    mock_vector_store.store_embeddings.return_value = MockVectorStoreMetrics(successful_inserts=1, failed_inserts=0)

    # Remove upsert method to simulate real vector store
    if hasattr(mock_vector_store, 'upsert'):
        delattr(mock_vector_store, 'upsert')

    job = ConceptEmbeddingRefreshJob(
        config=mock_config,
        neo4j_manager=mock_neo4j,
        embedding_generator=mock_embedding_gen,
        vector_store=mock_vector_store
    )

    # Test the upsert operation
    concept_name = "test_concept"
    embedding = [0.1, 0.2, 0.3, 0.4, 0.5]

    job._update_vector_store(concept_name, embedding)

    # Verify delete was called with correct concept block ID
    mock_vector_store.delete_chunks_by_block_id.assert_called_once_with("concept_test_concept")

    # Verify store_embeddings was called with one EmbeddedChunk
    mock_vector_store.store_embeddings.assert_called_once()
    call_args = mock_vector_store.store_embeddings.call_args[0][0]  # Get the list of embedded chunks
    assert len(call_args) == 1
    embedded_chunk = call_args[0]
    assert embedded_chunk.embedding == embedding
    assert embedded_chunk.model_name == "test-model"
    assert embedded_chunk.embedding_dim == len(embedding)
    assert embedded_chunk.chunk_metadata.aclarai_block_id == "concept_test_concept"
    assert embedded_chunk.chunk_metadata.chunk_index == 0


def test_update_vector_store_with_failed_insert():
    """Test the _update_vector_store method when insertion fails."""
    mock_config = MagicMock()
    mock_config.vault_path = "/tmp/test_vault"

    # Create mocks for dependencies
    mock_neo4j = Mock()
    mock_embedding_gen = Mock()
    mock_embedding_gen.model_name = "test-model"

    # Create a mock vector store that fails insertion
    mock_vector_store = Mock()
    mock_vector_store.delete_chunks_by_block_id.return_value = 0
    mock_vector_store.store_embeddings.return_value = MockVectorStoreMetrics(successful_inserts=0, failed_inserts=1)

    # Remove upsert method to simulate real vector store
    if hasattr(mock_vector_store, 'upsert'):
        delattr(mock_vector_store, 'upsert')

    job = ConceptEmbeddingRefreshJob(
        config=mock_config,
        neo4j_manager=mock_neo4j,
        embedding_generator=mock_embedding_gen,
        vector_store=mock_vector_store
    )

    # Test the upsert operation - should raise exception on failed insert
    concept_name = "test_concept"
    embedding = [0.1, 0.2, 0.3, 0.4, 0.5]

    try:
        job._update_vector_store(concept_name, embedding)
        raise AssertionError("Expected RuntimeError to be raised")
    except RuntimeError as e:
        assert "Failed to insert new embedding" in str(e)


if __name__ == "__main__":
    # Run basic tests
    print("Running concept refresh tests...")

    try:
        test_extract_semantic_text()
        test_extract_semantic_text_no_metadata()
        test_compute_hash()
        test_get_stored_embedding_hash_not_found()
        test_get_stored_embedding_hash_found()
        print("✓ All basic tests passed")
    except Exception as e:
        print(f"✗ Test failed: {e}")
        exit(1)

    print("All tests completed successfully!")

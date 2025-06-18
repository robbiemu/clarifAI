"""
Tests for the concept embedding refresh job.

This module tests the functionality of refreshing concept embeddings
from Tier 3 concept files following the specifications in
docs/arch/on-refreshing_concept_embeddings.md
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

from aclarai_scheduler.concept_refresh import ConceptEmbeddingRefreshJob


def test_extract_semantic_text():
    """Test semantic text extraction from concept file content."""
    with (
        patch("aclarai_scheduler.concept_refresh.Neo4jGraphManager"),
        patch("aclarai_scheduler.concept_refresh.EmbeddingGenerator"),
        patch("aclarai_scheduler.concept_refresh.aclaraiVectorStore"),
    ):
        # Create a mock config
        mock_config = MagicMock()
        mock_config.vault_path = "/tmp/test_vault"

        job = ConceptEmbeddingRefreshJob(mock_config)

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
    with (
        patch("aclarai_scheduler.concept_refresh.Neo4jGraphManager"),
        patch("aclarai_scheduler.concept_refresh.EmbeddingGenerator"),
        patch("aclarai_scheduler.concept_refresh.aclaraiVectorStore"),
    ):
        mock_config = MagicMock()
        mock_config.vault_path = "/tmp/test_vault"

        job = ConceptEmbeddingRefreshJob(mock_config)

        file_content = """# Deep Learning

Deep learning uses neural networks with multiple layers."""

        result = job._extract_semantic_text(file_content)
        assert result.strip() == file_content.strip()


def test_compute_hash():
    """Test SHA256 hash computation."""
    with (
        patch("aclarai_scheduler.concept_refresh.Neo4jGraphManager"),
        patch("aclarai_scheduler.concept_refresh.EmbeddingGenerator"),
        patch("aclarai_scheduler.concept_refresh.aclaraiVectorStore"),
    ):
        mock_config = MagicMock()
        mock_config.vault_path = "/tmp/test_vault"

        job = ConceptEmbeddingRefreshJob(mock_config)

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


@patch("aclarai_scheduler.concept_refresh.Neo4jGraphManager")
@patch("aclarai_scheduler.concept_refresh.EmbeddingGenerator")
@patch("aclarai_scheduler.concept_refresh.aclaraiVectorStore")
def test_process_concept_file_no_changes(
    _mock_vector_store, mock_embedding_gen, mock_neo4j
):
    """Test processing a concept file when no changes are detected."""
    # Create temporary vault directory
    with tempfile.TemporaryDirectory() as temp_dir:
        vault_path = Path(temp_dir)
        concepts_path = vault_path / "concepts"
        concepts_path.mkdir()

        # Create test config
        mock_config = MagicMock()
        mock_config.vault_path = str(vault_path)

        # Create mock Neo4j manager that returns existing hash
        mock_neo4j_instance = MagicMock()
        mock_neo4j.return_value = mock_neo4j_instance

        # Create test concept file
        concept_file = concepts_path / "test_concept.md"
        content = """# Test Concept

This is a test concept.

<!-- aclarai:id=concept_test_concept ver=1 -->
^concept_test_concept"""

        with open(concept_file, "w") as f:
            f.write(content)

        job = ConceptEmbeddingRefreshJob(mock_config)

        # Mock that the stored hash matches current hash
        semantic_text = job._extract_semantic_text(content)
        current_hash = job._compute_hash(semantic_text)
        job._get_stored_embedding_hash = Mock(return_value=current_hash)

        # Process the file
        processed, updated = job._process_concept_file(concept_file)

        assert processed is True
        assert updated is False  # No update needed

        # Verify that embedding was not generated
        mock_embedding_gen.return_value.embed_text.assert_not_called()


@patch("aclarai_scheduler.concept_refresh.Neo4jGraphManager")
@patch("aclarai_scheduler.concept_refresh.EmbeddingGenerator")
@patch("aclarai_scheduler.concept_refresh.aclaraiVectorStore")
def test_process_concept_file_with_changes(
    _mock_vector_store, mock_embedding_gen, _mock_neo4j
):
    """Test processing a concept file when changes are detected."""
    # Create temporary vault directory
    with tempfile.TemporaryDirectory() as temp_dir:
        vault_path = Path(temp_dir)
        concepts_path = vault_path / "concepts"
        concepts_path.mkdir()

        # Create test config
        mock_config = MagicMock()
        mock_config.vault_path = str(vault_path)

        # Create test concept file
        concept_file = concepts_path / "test_concept.md"
        content = """# Test Concept

This is a test concept with updated content.

<!-- aclarai:id=concept_test_concept ver=2 -->
^concept_test_concept"""

        with open(concept_file, "w") as f:
            f.write(content)

        job = ConceptEmbeddingRefreshJob(mock_config)

        # Mock that the stored hash is different (indicating changes)
        job._get_stored_embedding_hash = Mock(return_value="old_hash_value")
        job._update_vector_store = Mock()
        job._update_neo4j_metadata = Mock()

        # Mock embedding generation
        mock_embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        mock_embedding_gen.return_value.embed_text.return_value = mock_embedding

        # Process the file
        processed, updated = job._process_concept_file(concept_file)

        assert processed is True
        assert updated is True  # Update was needed

        # Verify that embedding was generated
        mock_embedding_gen.return_value.embed_text.assert_called_once()

        # Verify that vector store and Neo4j were updated
        job._update_vector_store.assert_called_once_with("test_concept", mock_embedding)
        job._update_neo4j_metadata.assert_called_once()


@patch("aclarai_scheduler.concept_refresh.Neo4jGraphManager")
@patch("aclarai_scheduler.concept_refresh.EmbeddingGenerator")
@patch("aclarai_scheduler.concept_refresh.aclaraiVectorStore")
def test_run_job_no_concepts_directory(
    _mock_vector_store, _mock_embedding_gen, _mock_neo4j
):
    """Test run_job when concepts directory doesn't exist."""
    # Create test config with non-existent concepts directory
    mock_config = MagicMock()
    mock_config.vault_path = "/nonexistent/vault"

    job = ConceptEmbeddingRefreshJob(mock_config)

    result = job.run_job()

    assert result["success"] is False
    assert result["concepts_processed"] == 0
    assert result["concepts_updated"] == 0
    assert "Concepts directory does not exist" in result["error_details"]


@patch("aclarai_scheduler.concept_refresh.Neo4jGraphManager")
@patch("aclarai_scheduler.concept_refresh.EmbeddingGenerator")
@patch("aclarai_scheduler.concept_refresh.aclaraiVectorStore")
def test_run_job_with_concept_files(_mock_vector_store, _mock_embedding_gen, _mock_neo4j):
    """Test run_job with actual concept files."""
    # Create temporary vault directory
    with tempfile.TemporaryDirectory() as temp_dir:
        vault_path = Path(temp_dir)
        concepts_path = vault_path / "concepts"
        concepts_path.mkdir()

        # Create test config
        mock_config = MagicMock()
        mock_config.vault_path = str(vault_path)

        # Create multiple test concept files
        concepts = [
            ("concept1.md", "# Concept 1\n\nFirst concept content."),
            ("concept2.md", "# Concept 2\n\nSecond concept content."),
        ]

        for filename, content in concepts:
            with open(concepts_path / filename, "w") as f:
                f.write(content)

        job = ConceptEmbeddingRefreshJob(mock_config)

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
    with (
        patch("aclarai_scheduler.concept_refresh.Neo4jGraphManager"),
        patch("aclarai_scheduler.concept_refresh.EmbeddingGenerator"),
        patch("aclarai_scheduler.concept_refresh.aclaraiVectorStore"),
    ):
        mock_config = MagicMock()
        mock_config.vault_path = "/tmp/test_vault"

        # Mock Neo4j manager session
        mock_session = MagicMock()
        mock_result = MagicMock()
        mock_result.single.return_value = None
        mock_session.run.return_value = mock_result

        mock_neo4j_manager = MagicMock()
        mock_neo4j_manager.session.return_value.__enter__.return_value = mock_session

        job = ConceptEmbeddingRefreshJob(mock_config)
        job.neo4j_manager = mock_neo4j_manager

        result = job._get_stored_embedding_hash("nonexistent_concept")

        assert result is None


def test_get_stored_embedding_hash_found():
    """Test getting stored embedding hash when concept exists."""
    with (
        patch("aclarai_scheduler.concept_refresh.Neo4jGraphManager"),
        patch("aclarai_scheduler.concept_refresh.EmbeddingGenerator"),
        patch("aclarai_scheduler.concept_refresh.aclaraiVectorStore"),
    ):
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

        job = ConceptEmbeddingRefreshJob(mock_config)
        job.neo4j_manager = mock_neo4j_manager

        result = job._get_stored_embedding_hash("existing_concept")

        assert result == "stored_hash_value"


if __name__ == "__main__":
    # Run basic tests
    print("Running concept refresh tests...")

    try:
        test_extract_semantic_text()
        test_extract_semantic_text_no_metadata()
        test_compute_hash()
        print("✓ All basic tests passed")
    except Exception as e:
        print(f"✗ Test failed: {e}")
        exit(1)

    print("All tests completed successfully!")

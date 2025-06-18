"""
Integration tests for ConceptProcessor with Tier 3 file generation.
"""

import tempfile
import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from datetime import datetime, timezone

from clarifai_shared.config import ClarifAIConfig, VaultPaths
from clarifai_shared.graph.models import Concept
from clarifai_shared.concept_detection.models import (
    ConceptAction,
    ConceptDetectionResult,
    ConceptDetectionBatch,
)
from clarifai_shared.tier3_concept import ConceptFileWriter

# Skip spaCy model loading for these tests
@pytest.fixture(autouse=True)
def mock_spacy_model():
    """Mock spaCy model loading to avoid network dependencies."""
    with patch("spacy.load") as mock_load:
        mock_nlp = Mock()
        mock_load.return_value = mock_nlp
        yield mock_nlp

# Skip embedding model loading for these tests  
@pytest.fixture(autouse=True)
def mock_embedding_models():
    """Mock embedding model loading to avoid network dependencies."""
    with patch("llama_index.embeddings.huggingface.HuggingFaceEmbedding") as mock_hf:
        mock_embedding = Mock()
        mock_hf.return_value = mock_embedding
        yield mock_embedding


class TestConceptProcessorTier3Integration:
    """
    Test ConceptProcessor integration with Tier 3 file creation.

    Note: These tests mock dependencies to avoid network access requirements.
    """

    @patch("clarifai_shared.graph.neo4j_manager.Neo4jGraphManager")
    @patch("clarifai_shared.concept_detection.detector.ConceptDetector")
    @patch("clarifai_shared.noun_phrase_extraction.extractor.NounPhraseExtractor")
    @patch("clarifai_shared.noun_phrase_extraction.concept_candidates_store.ConceptCandidatesVectorStore")
    def test_promoted_concepts_create_tier3_files(
        self, mock_store, mock_extractor, mock_detector, mock_neo4j_manager
    ):
        """Test that promoted concepts create both Neo4j nodes and Tier 3 files."""
        
        # Check if HuggingFace models are accessible
        try:
            import urllib.request
            urllib.request.urlopen("https://huggingface.co", timeout=1)
        except Exception:
            pytest.skip("Skipping test due to network restrictions (cannot access HuggingFace models)")
        
        try:
            # Try importing ConceptProcessor - will fail if dependencies unavailable
            import sys
            sys.path.append("/home/runner/work/clarifAI/clarifAI/services/clarifai-core")
            from clarifai_core.concept_processor import ConceptProcessor
        except (ImportError, OSError) as e:
            pytest.skip(f"ConceptProcessor dependencies unavailable: {e}")

        with tempfile.TemporaryDirectory() as temp_dir:
            # Setup config with temp directory
            config = ClarifAIConfig(
                vault_path=temp_dir, paths=VaultPaths(concepts="concepts")
            )

            # Setup mocks
            mock_store_instance = Mock()
            mock_store.return_value = mock_store_instance
            mock_store_instance.update_candidate_status.return_value = True

            mock_extractor_instance = Mock()
            mock_extractor.return_value = mock_extractor_instance

            mock_detector_instance = Mock()
            mock_detector.return_value = mock_detector_instance

            # Mock concept detection results with a promoted concept
            promoted_result = ConceptDetectionResult(
                candidate_id="test_candidate_1",
                candidate_text="machine learning",
                action=ConceptAction.PROMOTED,
                confidence=0.95,
                reason="No similar concepts found",
            )

            detection_batch = ConceptDetectionBatch(
                results=[promoted_result],
                total_processed=1,
                merged_count=0,
                promoted_count=1,
                processing_time=0.1,
                error=None,
            )

            mock_detector_instance.process_candidates_batch.return_value = (
                detection_batch
            )

            # Mock Neo4j manager to return created concepts
            mock_neo4j_instance = Mock()
            mock_neo4j_manager.return_value = mock_neo4j_instance

            created_concept = Concept(
                concept_id="concept_test123",
                text="machine learning",
                source_candidate_id="test_candidate_1",
                source_node_id="claim_456",
                source_node_type="claim",
                clarifai_id="doc_789",
                version=1,
                timestamp=datetime.now(timezone.utc),
            )

            mock_neo4j_instance.create_concepts.return_value = [created_concept]

            # Initialize ConceptProcessor
            processor = ConceptProcessor(config)

            # Create candidate metadata map
            candidate_metadata_map = {
                "test_candidate_1": {
                    "source_node_id": "claim_456",
                    "source_node_type": "claim",
                    "clarifai_id": "doc_789",
                    "text": "machine learning",
                }
            }

            # Call the method that updates candidate statuses
            updates = processor._update_candidate_statuses(
                detection_batch, candidate_metadata_map
            )

            # Verify Neo4j concept creation was called
            mock_neo4j_instance.create_concepts.assert_called_once()
            created_concepts_arg = mock_neo4j_instance.create_concepts.call_args[0][0]
            assert len(created_concepts_arg) == 1
            assert created_concepts_arg[0].text == "machine learning"

            # Verify Tier 3 file was created
            concepts_dir = Path(temp_dir) / "concepts"
            expected_file = concepts_dir / "machine_learning.md"
            assert expected_file.exists(), (
                f"Expected file {expected_file} was not created"
            )

            # Verify file content
            content = expected_file.read_text()
            assert "## Concept: machine learning" in content
            assert "<!-- clarifai:id=concept_test123 ver=1 -->" in content
            assert "^concept_test123" in content

            # Verify updates include concept_id
            assert len(updates) == 1
            assert updates[0]["concept_id"] == "concept_test123"

    @patch("clarifai_shared.graph.neo4j_manager.Neo4jGraphManager")
    @patch("clarifai_shared.concept_detection.detector.ConceptDetector")
    @patch("clarifai_shared.noun_phrase_extraction.extractor.NounPhraseExtractor")
    @patch("clarifai_shared.noun_phrase_extraction.concept_candidates_store.ConceptCandidatesVectorStore")
    def test_no_tier3_files_for_merged_concepts(
        self, mock_store, mock_extractor, mock_detector, mock_neo4j_manager
    ):
        """Test that merged concepts don't create Tier 3 files."""
        
        # Check if HuggingFace models are accessible
        try:
            import urllib.request
            urllib.request.urlopen("https://huggingface.co", timeout=1)
        except Exception:
            pytest.skip("Skipping test due to network restrictions (cannot access HuggingFace models)")
        
        try:
            # Try importing ConceptProcessor - will fail if dependencies unavailable
            import sys
            sys.path.append("/home/runner/work/clarifAI/clarifAI/services/clarifai-core")
            from clarifai_core.concept_processor import ConceptProcessor
        except (ImportError, OSError) as e:
            pytest.skip(f"ConceptProcessor dependencies unavailable: {e}")

        with tempfile.TemporaryDirectory() as temp_dir:
            # Setup config with temp directory
            config = ClarifAIConfig(
                vault_path=temp_dir, paths=VaultPaths(concepts="concepts")
            )

            # Setup mocks
            mock_store_instance = Mock()
            mock_store.return_value = mock_store_instance
            mock_store_instance.update_candidate_status.return_value = True

            mock_extractor_instance = Mock()
            mock_extractor.return_value = mock_extractor_instance

            mock_detector_instance = Mock()
            mock_detector.return_value = mock_detector_instance

            # Mock concept detection results with a merged concept (no promotion)
            from clarifai_shared.concept_detection.models import SimilarityMatch

            best_match = SimilarityMatch(
                candidate_id="test_candidate_1",
                matched_concept_id="existing_concept",
                matched_candidate_id="existing_concept_candidate",
                similarity_score=0.95,
                matched_text="machine learning",
            )

            merged_result = ConceptDetectionResult(
                candidate_id="test_candidate_1",
                candidate_text="machine learning",
                action=ConceptAction.MERGED,
                similarity_matches=[best_match],
                confidence=0.95,
                reason="Similar concept found",
            )

            detection_batch = ConceptDetectionBatch(
                results=[merged_result],
                total_processed=1,
                merged_count=1,
                promoted_count=0,
                processing_time=0.1,
                error=None,
            )

            mock_detector_instance.process_candidates_batch.return_value = (
                detection_batch
            )

            # Mock Neo4j manager (should not be called)
            mock_neo4j_instance = Mock()
            mock_neo4j_manager.return_value = mock_neo4j_instance

            # Initialize ConceptProcessor
            processor = ConceptProcessor(config)

            # Create candidate metadata map
            candidate_metadata_map = {
                "test_candidate_1": {
                    "source_node_id": "claim_456",
                    "source_node_type": "claim",
                    "clarifai_id": "doc_789",
                    "text": "machine learning",
                }
            }

            # Call the method that updates candidate statuses
            updates = processor._update_candidate_statuses(
                detection_batch, candidate_metadata_map
            )

            # Verify Neo4j concept creation was NOT called (no promoted concepts)
            mock_neo4j_instance.create_concepts.assert_not_called()

            # Verify no Tier 3 files were created
            concepts_dir = Path(temp_dir) / "concepts"
            if concepts_dir.exists():
                concept_files = list(concepts_dir.glob("*.md"))
                assert len(concept_files) == 0, (
                    f"Unexpected concept files created: {concept_files}"
                )

            # Verify updates don't include concept_id for merged concepts
            assert len(updates) == 1
            assert "concept_id" not in updates[0]
            assert updates[0]["new_status"] == "merged"


@pytest.mark.integration
class TestConceptFileWriterIntegration:
    """Additional integration tests specifically for ConceptFileWriter."""

    def test_concept_file_writer_integration(self):
        """Test that ConceptFileWriter correctly creates Tier 3 files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Setup config with temp directory
            config = ClarifAIConfig(
                vault_path=temp_dir, paths=VaultPaths(concepts="concepts")
            )

            # Initialize ConceptFileWriter
            writer = ConceptFileWriter(config)

            # Create a test concept
            concept = Concept(
                concept_id="concept_test123",
                text="machine learning",
                source_candidate_id="test_candidate_1",
                source_node_id="claim_456",
                source_node_type="claim",
                clarifai_id="doc_789",
                version=1,
                timestamp=datetime.now(timezone.utc),
            )

            # Write the concept file
            success = writer.write_concept_file(concept)
            assert success, "ConceptFileWriter should return True for successful write"

            # Verify Tier 3 file was created
            concepts_dir = Path(temp_dir) / "concepts"
            expected_file = concepts_dir / "machine_learning.md"
            assert expected_file.exists(), (
                f"Expected file {expected_file} was not created"
            )

            # Verify file content
            content = expected_file.read_text()
            assert "## Concept: machine learning" in content
            assert "<!-- clarifai:id=concept_test123 ver=1 -->" in content
            assert "^concept_test123" in content
            assert "This concept was automatically extracted" in content

    def test_concept_file_writer_error_handling(self):
        """Test that ConceptFileWriter handles errors gracefully."""
        # Use a non-existent directory to simulate write errors
        config = ClarifAIConfig(
            vault_path="/nonexistent/path", paths=VaultPaths(concepts="concepts")
        )

        writer = ConceptFileWriter(config)

        concept = Concept(
            concept_id="concept_test123",
            text="machine learning",
            source_candidate_id="test_candidate_1",
            source_node_id="claim_456",
            source_node_type="claim",
            clarifai_id="doc_789",
            version=1,
            timestamp=datetime.now(timezone.utc),
        )

        # Write should fail gracefully and return False
        success = writer.write_concept_file(concept)
        assert not success, "ConceptFileWriter should return False for failed write"

    def test_multiple_concepts_integration(self):
        """Test writing multiple concept files in sequence."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = ClarifAIConfig(
                vault_path=temp_dir, paths=VaultPaths(concepts="concepts")
            )

            writer = ConceptFileWriter(config)

            # Create multiple test concepts
            concepts = [
                Concept(
                    concept_id="concept_ml123",
                    text="machine learning",
                    source_candidate_id="candidate_1",
                    source_node_id="claim_456",
                    source_node_type="claim",
                    clarifai_id="doc_789",
                    version=1,
                    timestamp=datetime.now(timezone.utc),
                ),
                Concept(
                    concept_id="concept_ai456",
                    text="artificial intelligence",
                    source_candidate_id="candidate_2",
                    source_node_id="claim_789",
                    source_node_type="claim",
                    clarifai_id="doc_012",
                    version=1,
                    timestamp=datetime.now(timezone.utc),
                ),
            ]

            # Write all concepts
            for concept in concepts:
                success = writer.write_concept_file(concept)
                assert success, f"Failed to write concept file for {concept.text}"

            # Verify all files were created
            concepts_dir = Path(temp_dir) / "concepts"
            assert (concepts_dir / "machine_learning.md").exists()
            assert (concepts_dir / "artificial_intelligence.md").exists()

            # Verify each file has correct content
            ml_content = (concepts_dir / "machine_learning.md").read_text()
            assert "## Concept: machine learning" in ml_content
            assert "concept_ml123" in ml_content

            ai_content = (concepts_dir / "artificial_intelligence.md").read_text()
            assert "## Concept: artificial intelligence" in ai_content
            assert "concept_ai456" in ai_content

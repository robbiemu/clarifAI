"""
Tests for concept detection using hnswlib.
This module tests the core functionality of concept detection including
similarity matching and merge/promote decision logic.
"""

from unittest.mock import Mock, patch

import pytest
from aclarai_shared.concept_detection import (
    ConceptDetectionResult,
    ConceptDetector,
    SimilarityMatch,
)
from aclarai_shared.concept_detection.models import ConceptAction
from aclarai_shared.config import ConceptsConfig, aclaraiConfig
from aclarai_shared.noun_phrase_extraction.models import NounPhraseCandidate


class TestConceptDetector:
    """Test suite for ConceptDetector class."""

    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing."""
        config = Mock(spec=aclaraiConfig)
        config.concepts = Mock(spec=ConceptsConfig)
        config.concepts.similarity_threshold = 0.9
        return config

    @pytest.fixture
    def mock_candidates_store(self):
        """Mock concept candidates store."""
        with patch(
            "aclarai_shared.concept_detection.detector.ConceptCandidatesVectorStore"
        ) as mock_store_class:
            mock_store = Mock()
            mock_store.embed_dim = 384  # Typical embedding dimension
            mock_store.get_candidates_by_status.return_value = []
            mock_store_class.return_value = mock_store
            yield mock_store

    @pytest.fixture
    def detector(self, mock_config, _mock_candidates_store):
        """Create a ConceptDetector instance for testing."""
        with patch(
            "aclarai_shared.concept_detection.detector.load_config",
            return_value=mock_config,
        ):
            detector = ConceptDetector(config=mock_config)
            return detector

    @pytest.fixture
    def sample_candidate(self):
        """Create a sample noun phrase candidate."""
        return NounPhraseCandidate(
            text="machine learning",
            normalized_text="machine learning",
            source_node_id="claim_123",
            source_node_type="claim",
            aclarai_id="blk_456",
            embedding=[0.1] * 384,  # Mock embedding
            status="pending",
        )

    @pytest.fixture
    def similar_candidate(self):
        """Create a similar candidate for testing."""
        return NounPhraseCandidate(
            text="Machine Learning",
            normalized_text="machine learning",
            source_node_id="claim_124",
            source_node_type="claim",
            aclarai_id="blk_457",
            embedding=[0.11] * 384,  # Slightly different but similar embedding
            status="pending",
        )

    @pytest.fixture
    def different_candidate(self):
        """Create a very different candidate for testing."""
        return NounPhraseCandidate(
            text="database schema",
            normalized_text="database schema",
            source_node_id="claim_125",
            source_node_type="claim",
            aclarai_id="blk_458",
            embedding=[-0.5] * 384,  # Very different embedding
            status="pending",
        )

    def test_initialization(self, detector, mock_config):
        """Test ConceptDetector initialization."""
        assert detector.config == mock_config
        assert detector.similarity_threshold == 0.9
        assert detector.embedding_dim == 384
        assert detector.index is None
        assert detector.id_to_metadata == {}
        assert detector.next_id == 0

    @patch("aclarai_shared.concept_detection.detector.hnswlib.Index")
    def test_initialize_index(self, mock_hnswlib_index, detector):
        """Test HNSW index initialization."""
        mock_index = Mock()
        mock_hnswlib_index.return_value = mock_index
        detector._initialize_index(max_elements=1000)
        mock_hnswlib_index.assert_called_once_with(space="cosine", dim=384)
        mock_index.init_index.assert_called_once_with(
            max_elements=1000, M=16, ef_construction=200, random_seed=42
        )
        mock_index.set_ef.assert_called_once_with(50)
        assert detector.index == mock_index

    def test_build_index_empty_candidates(self, detector, mock_candidates_store):
        """Test building index with no candidates."""
        mock_candidates_store.get_candidates_by_status.return_value = []
        with patch.object(detector, "_initialize_index") as mock_init:
            result = detector.build_index_from_candidates()
            assert result == 0
            mock_init.assert_called_once_with(max_elements=1000)

    def test_build_index_with_candidates(self, detector, _mock_candidates_store):
        """Test building index with candidates."""
        # Mock candidates data
        mock_candidates = [
            {
                "id": "cand_1",
                "normalized_text": "machine learning",
                "embedding": [0.1] * 384,
                "status": "pending",
            },
            {
                "id": "cand_2",
                "normalized_text": "deep learning",
                "embedding": [0.2] * 384,
                "status": "pending",
            },
        ]
        # Configure the mock store to return our test candidates
        detector.candidates_store.get_candidates_by_status.return_value = (
            mock_candidates
        )
        with patch(
            "aclarai_shared.concept_detection.detector.hnswlib.Index"
        ) as mock_hnswlib:
            mock_index = Mock()
            mock_hnswlib.return_value = mock_index
            result = detector.build_index_from_candidates()
            assert result == 2
            # Verify the mock was used
            mock_hnswlib.assert_called_once_with(space="cosine", dim=384)
            mock_index.init_index.assert_called_once()
            mock_index.add_items.assert_called_once()
            assert len(detector.id_to_metadata) == 2

    def test_find_similar_candidates_no_index(self, detector, sample_candidate):
        """Test finding similar candidates when no index exists."""
        with patch.object(detector, "build_index_from_candidates", return_value=0):
            result = detector.find_similar_candidates(sample_candidate)
            assert result == []

    def test_find_similar_candidates_no_embedding(
        self, detector, _mock_candidates_store
    ):
        """Test finding similar candidates for candidate without embedding."""
        candidate_no_embedding = NounPhraseCandidate(
            text="test",
            normalized_text="test",
            source_node_id="claim_123",
            source_node_type="claim",
            aclarai_id="blk_456",
            embedding=None,
            status="pending",
        )
        detector.index = Mock()  # Mock index exists
        result = detector.find_similar_candidates(candidate_no_embedding)
        assert result == []

    def test_detect_concept_action_promote(self, detector, sample_candidate):
        """Test concept action detection when candidate should be promoted."""
        with patch.object(detector, "find_similar_candidates", return_value=[]):
            result = detector.detect_concept_action(sample_candidate)
            assert result.action == ConceptAction.PROMOTED
            assert result.confidence == 1.0
            assert "No similar candidates found" in result.reason
            assert result.candidate_text == "machine learning"

    def test_detect_concept_action_merge(self, detector, sample_candidate):
        """Test concept action detection when candidate should be merged."""
        # Mock a high similarity match
        mock_match = SimilarityMatch(
            candidate_id="test",
            matched_candidate_id="existing_123",
            matched_concept_id=None,
            similarity_score=0.95,  # Above threshold
            matched_text="machine learning algorithms",
            metadata={},
        )
        with patch.object(
            detector, "find_similar_candidates", return_value=[mock_match]
        ):
            result = detector.detect_concept_action(sample_candidate)
            assert result.action == ConceptAction.MERGED
            assert result.confidence == 0.95
            assert "Found similar candidate" in result.reason
            assert len(result.similarity_matches) == 1

    def test_detect_concept_action_below_threshold(self, detector, sample_candidate):
        """Test concept action detection when similarity is below threshold."""
        # Mock a low similarity match
        mock_match = SimilarityMatch(
            candidate_id="test",
            matched_candidate_id="existing_123",
            matched_concept_id=None,
            similarity_score=0.7,  # Below threshold of 0.9
            matched_text="neural networks",
            metadata={},
        )
        with patch.object(
            detector, "find_similar_candidates", return_value=[mock_match]
        ):
            result = detector.detect_concept_action(sample_candidate)
            assert result.action == ConceptAction.PROMOTED
            assert "Best similarity 0.700 < 0.9" in result.reason
            assert len(result.similarity_matches) == 1

    def test_process_candidates_batch(self, detector):
        """Test processing a batch of candidates."""
        candidates = [
            NounPhraseCandidate(
                text="ai",
                normalized_text="ai",
                source_node_id="claim_1",
                source_node_type="claim",
                aclarai_id="blk_1",
                embedding=[0.1] * 384,
                status="pending",
            ),
            NounPhraseCandidate(
                text="artificial intelligence",
                normalized_text="artificial intelligence",
                source_node_id="claim_2",
                source_node_type="claim",
                aclarai_id="blk_2",
                embedding=[0.11] * 384,  # Similar to first
                status="pending",
            ),
        ]
        # Mock the individual detection results
        mock_results = [
            ConceptDetectionResult(
                candidate_id="claim_1_ai",
                candidate_text="ai",
                action=ConceptAction.PROMOTED,
                confidence=1.0,
            ),
            ConceptDetectionResult(
                candidate_id="claim_2_artificial intelligence",
                candidate_text="artificial intelligence",
                action=ConceptAction.MERGED,
                confidence=0.95,
            ),
        ]
        with (
            patch.object(detector, "build_index_from_candidates"),
            patch.object(detector, "detect_concept_action", side_effect=mock_results),
        ):
            batch_result = detector.process_candidates_batch(candidates)
            assert batch_result.is_successful
            assert batch_result.total_processed == 2
            assert batch_result.merged_count == 1
            assert batch_result.promoted_count == 1
            assert len(batch_result.results) == 2
            assert batch_result.processing_time is not None

    def test_similarity_threshold_from_config(
        self, mock_config, _mock_candidates_store
    ):
        """Test that similarity threshold is correctly read from config."""
        mock_config.concepts.similarity_threshold = 0.85
        with patch(
            "aclarai_shared.concept_detection.detector.load_config",
            return_value=mock_config,
        ):
            detector = ConceptDetector(config=mock_config)
            assert detector.similarity_threshold == 0.85

    def test_error_handling_in_detection(self, detector, sample_candidate):
        """Test error handling during concept detection."""
        with patch.object(
            detector, "find_similar_candidates", side_effect=Exception("Test error")
        ):
            result = detector.detect_concept_action(sample_candidate)
            assert result.action == ConceptAction.PROMOTED  # Fallback
            assert result.confidence == 0.0
            assert "Error during detection" in result.reason

    def test_batch_error_handling(self, detector):
        """Test error handling during batch processing."""
        candidates = [Mock()]
        with patch.object(
            detector, "build_index_from_candidates", side_effect=Exception("Test error")
        ):
            batch_result = detector.process_candidates_batch(candidates)
            assert not batch_result.is_successful
            assert "Test error" in batch_result.error
            assert batch_result.total_processed == 1
            assert batch_result.processing_time is not None

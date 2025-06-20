"""Test concept detection models."""

from aclarai_shared.concept_detection.models import (
    ConceptAction,
    ConceptDetectionBatch,
    ConceptDetectionResult,
    SimilarityMatch,
)


class TestConceptDetectionModels:
    """Test suite for concept detection data models."""

    def test_concept_action_enum(self):
        """Test ConceptAction enum values."""
        assert ConceptAction.MERGED.value == "merged"
        assert ConceptAction.PROMOTED.value == "promoted"

    def test_similarity_match_creation(self):
        """Test SimilarityMatch creation."""
        match = SimilarityMatch(
            candidate_id="cand_123",
            matched_concept_id="concept_456",
            matched_candidate_id=None,
            similarity_score=0.95,
            matched_text="machine learning",
            metadata={"source": "test"},
        )
        assert match.candidate_id == "cand_123"
        assert match.matched_concept_id == "concept_456"
        assert match.matched_candidate_id is None
        assert match.similarity_score == 0.95
        assert match.matched_text == "machine learning"
        assert match.metadata["source"] == "test"

    def test_concept_detection_result_best_match(self):
        """Test ConceptDetectionResult best_match property."""
        matches = [
            SimilarityMatch(
                candidate_id="cand_1",
                matched_candidate_id="match_1",
                matched_concept_id=None,
                similarity_score=0.7,
                matched_text="text1",
            ),
            SimilarityMatch(
                candidate_id="cand_1",
                matched_candidate_id="match_2",
                matched_concept_id=None,
                similarity_score=0.9,
                matched_text="text2",
            ),
            SimilarityMatch(
                candidate_id="cand_1",
                matched_candidate_id="match_3",
                matched_concept_id=None,
                similarity_score=0.8,
                matched_text="text3",
            ),
        ]
        result = ConceptDetectionResult(
            candidate_id="cand_1",
            candidate_text="test",
            action=ConceptAction.MERGED,
            similarity_matches=matches,
        )
        best_match = result.best_match
        assert best_match is not None
        assert best_match.similarity_score == 0.9
        assert best_match.matched_text == "text2"

    def test_concept_detection_result_no_matches(self):
        """Test ConceptDetectionResult with no matches."""
        result = ConceptDetectionResult(
            candidate_id="cand_1", candidate_text="test", action=ConceptAction.PROMOTED
        )
        assert result.best_match is None
        assert len(result.similarity_matches) == 0

    def test_concept_detection_batch_success_properties(self):
        """Test ConceptDetectionBatch success properties."""
        results = [
            ConceptDetectionResult(
                candidate_id="cand_1",
                candidate_text="test1",
                action=ConceptAction.MERGED,
            ),
            ConceptDetectionResult(
                candidate_id="cand_2",
                candidate_text="test2",
                action=ConceptAction.PROMOTED,
            ),
            ConceptDetectionResult(
                candidate_id="cand_3",
                candidate_text="test3",
                action=ConceptAction.MERGED,
            ),
        ]
        batch = ConceptDetectionBatch(
            results=results,
            total_processed=3,
            merged_count=2,
            promoted_count=1,
            processing_time=1.5,
        )
        assert batch.is_successful
        assert batch.merge_rate == 2 / 3
        assert batch.promotion_rate == 1 / 3

    def test_concept_detection_batch_with_error(self):
        """Test ConceptDetectionBatch with error."""
        batch = ConceptDetectionBatch(total_processed=5, error="Processing failed")
        assert not batch.is_successful
        assert batch.merge_rate == 0.0  # No counts set
        assert batch.promotion_rate == 0.0

    def test_concept_detection_batch_zero_processed(self):
        """Test ConceptDetectionBatch with zero processed items."""
        batch = ConceptDetectionBatch(
            total_processed=0, merged_count=0, promoted_count=0
        )
        assert batch.merge_rate == 0.0
        assert batch.promotion_rate == 0.0

"""
Tests for Claimify pipeline data models.

Tests the core data structures used throughout the Claimify pipeline.
"""

import unittest

# Import the data models
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from clarifai_shared.claimify.data_models import (
    SentenceChunk,
    ClaimifyContext,
    SelectionResult,
    DisambiguationResult,
    ClaimCandidate,
    DecompositionResult,
    ClaimifyResult,
    ClaimifyConfig,
    NodeType,
)


class TestSentenceChunk(unittest.TestCase):
    """Test SentenceChunk data model."""

    def test_sentence_chunk_creation(self):
        """Test basic SentenceChunk creation."""
        chunk = SentenceChunk(
            text="This is a test sentence.",
            source_id="blk_001",
            chunk_id="chunk_001",
            sentence_index=0,
        )

        self.assertEqual(chunk.text, "This is a test sentence.")
        self.assertEqual(chunk.source_id, "blk_001")
        self.assertEqual(chunk.chunk_id, "chunk_001")
        self.assertEqual(chunk.sentence_index, 0)


class TestClaimifyContext(unittest.TestCase):
    """Test ClaimifyContext data model."""

    def setUp(self):
        """Set up test data."""
        self.current_sentence = SentenceChunk(
            text="This is the current sentence.",
            source_id="blk_001",
            chunk_id="chunk_002",
            sentence_index=1,
        )

        self.preceding_sentence = SentenceChunk(
            text="This is a preceding sentence.",
            source_id="blk_001",
            chunk_id="chunk_001",
            sentence_index=0,
        )

        self.following_sentence = SentenceChunk(
            text="This is a following sentence.",
            source_id="blk_001",
            chunk_id="chunk_003",
            sentence_index=2,
        )

    def test_context_creation(self):
        """Test ClaimifyContext creation."""
        context = ClaimifyContext(
            current_sentence=self.current_sentence,
            preceding_sentences=[self.preceding_sentence],
            following_sentences=[self.following_sentence],
        )

        self.assertEqual(context.current_sentence, self.current_sentence)
        self.assertEqual(len(context.preceding_sentences), 1)
        self.assertEqual(len(context.following_sentences), 1)
        self.assertEqual(context.context_window_size, (1, 1))

    def test_empty_context(self):
        """Test context with no surrounding sentences."""
        context = ClaimifyContext(current_sentence=self.current_sentence)

        self.assertEqual(len(context.preceding_sentences), 0)
        self.assertEqual(len(context.following_sentences), 0)
        self.assertEqual(context.context_window_size, (0, 0))


class TestClaimCandidate(unittest.TestCase):
    """Test ClaimCandidate data model."""

    def test_valid_claim_candidate(self):
        """Test a claim candidate that passes all criteria."""
        candidate = ClaimCandidate(
            text="The system reported an error.",
            is_atomic=True,
            is_self_contained=True,
            is_verifiable=True,
            confidence=0.9,
        )

        self.assertTrue(candidate.passes_criteria)
        self.assertEqual(candidate.node_type, NodeType.CLAIM)

    def test_invalid_claim_candidate(self):
        """Test a claim candidate that fails criteria."""
        candidate = ClaimCandidate(
            text="It caused an error and the user was confused.",
            is_atomic=False,  # Not atomic due to compound structure
            is_self_contained=False,  # "It" is ambiguous
            is_verifiable=True,
            confidence=0.6,
        )

        self.assertFalse(candidate.passes_criteria)
        self.assertEqual(candidate.node_type, NodeType.SENTENCE)

    def test_partial_failure(self):
        """Test a candidate that fails some but not all criteria."""
        candidate = ClaimCandidate(
            text="The error occurred.",
            is_atomic=True,
            is_self_contained=True,
            is_verifiable=False,  # Not specific enough to be verifiable
            confidence=0.7,
        )

        self.assertFalse(candidate.passes_criteria)
        self.assertEqual(candidate.node_type, NodeType.SENTENCE)


class TestDecompositionResult(unittest.TestCase):
    """Test DecompositionResult data model."""

    def test_decomposition_result_filtering(self):
        """Test filtering of valid claims vs sentence nodes."""
        valid_claim = ClaimCandidate(
            text="The system reported an error.",
            is_atomic=True,
            is_self_contained=True,
            is_verifiable=True,
        )

        invalid_claim = ClaimCandidate(
            text="It was problematic.",
            is_atomic=True,
            is_self_contained=False,  # "It" is ambiguous
            is_verifiable=True,
        )

        result = DecompositionResult(
            original_text="The system reported an error. It was problematic.",
            claim_candidates=[valid_claim, invalid_claim],
        )

        self.assertEqual(len(result.valid_claims), 1)
        self.assertEqual(len(result.sentence_nodes), 1)
        self.assertEqual(result.valid_claims[0].text, "The system reported an error.")
        self.assertEqual(result.sentence_nodes[0].text, "It was problematic.")


class TestClaimifyResult(unittest.TestCase):
    """Test ClaimifyResult data model."""

    def setUp(self):
        """Set up test data."""
        self.sentence = SentenceChunk(
            text="The user received an error from the system.",
            source_id="blk_001",
            chunk_id="chunk_001",
            sentence_index=0,
        )

        self.context = ClaimifyContext(current_sentence=self.sentence)

    def test_unprocessed_result(self):
        """Test result for sentence that was not selected."""
        selection_result = SelectionResult(
            sentence_chunk=self.sentence,
            is_selected=False,
            reasoning="No verifiable content found",
        )

        result = ClaimifyResult(
            original_chunk=self.sentence,
            context=self.context,
            selection_result=selection_result,
        )

        self.assertFalse(result.was_processed)
        self.assertEqual(len(result.final_claims), 0)
        self.assertEqual(len(result.final_sentences), 0)

    def test_processed_result_with_claims(self):
        """Test result for sentence that produced valid claims."""
        selection_result = SelectionResult(
            sentence_chunk=self.sentence,
            is_selected=True,
            reasoning="Contains verifiable error information",
        )

        disambiguation_result = DisambiguationResult(
            original_sentence=self.sentence,
            disambiguated_text="The user received an error from the system.",
            changes_made=[],
        )

        valid_claim = ClaimCandidate(
            text="The user received an error from the system.",
            is_atomic=True,
            is_self_contained=True,
            is_verifiable=True,
        )

        decomposition_result = DecompositionResult(
            original_text="The user received an error from the system.",
            claim_candidates=[valid_claim],
        )

        result = ClaimifyResult(
            original_chunk=self.sentence,
            context=self.context,
            selection_result=selection_result,
            disambiguation_result=disambiguation_result,
            decomposition_result=decomposition_result,
        )

        self.assertTrue(result.was_processed)
        self.assertEqual(len(result.final_claims), 1)
        self.assertEqual(len(result.final_sentences), 0)
        self.assertEqual(
            result.final_claims[0].text, "The user received an error from the system."
        )


class TestClaimifyConfig(unittest.TestCase):
    """Test ClaimifyConfig data model."""

    def test_default_config(self):
        """Test default configuration values."""
        config = ClaimifyConfig()

        self.assertEqual(config.context_window_p, 3)
        self.assertEqual(config.context_window_f, 1)
        self.assertEqual(config.default_model, "gpt-3.5-turbo")
        self.assertIsNone(config.selection_model)
        self.assertEqual(config.max_retries, 3)
        self.assertEqual(config.temperature, 0.1)

    def test_custom_config(self):
        """Test custom configuration values."""
        config = ClaimifyConfig(
            context_window_p=5,
            context_window_f=2,
            selection_model="gpt-4",
            disambiguation_model="claude-3-opus",
            decomposition_model="gpt-4",
            temperature=0.2,
        )

        self.assertEqual(config.context_window_p, 5)
        self.assertEqual(config.context_window_f, 2)
        self.assertEqual(config.get_model_for_stage("selection"), "gpt-4")
        self.assertEqual(config.get_model_for_stage("disambiguation"), "claude-3-opus")
        self.assertEqual(config.get_model_for_stage("decomposition"), "gpt-4")
        self.assertEqual(config.temperature, 0.2)

    def test_model_fallback(self):
        """Test fallback to default model when stage model not configured."""
        config = ClaimifyConfig(
            default_model="custom-model",
            selection_model="gpt-4",  # Only selection model configured
        )

        self.assertEqual(config.get_model_for_stage("selection"), "gpt-4")
        self.assertEqual(config.get_model_for_stage("disambiguation"), "custom-model")
        self.assertEqual(config.get_model_for_stage("decomposition"), "custom-model")


if __name__ == "__main__":
    unittest.main()

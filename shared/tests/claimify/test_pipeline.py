"""
Tests for the main Claimify pipeline.

Tests the ClaimifyPipeline orchestrator and end-to-end processing.
"""

# import unittest
from unittest.mock import Mock

# Import the pipeline classes
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from clarifai_shared.claimify.pipeline import ClaimifyPipeline
from clarifai_shared.claimify.data_models import (
    SentenceChunk,
    ClaimifyContext,
    ClaimifyConfig,
)


class TestClaimifyPipeline:
    """Test ClaimifyPipeline functionality."""

    def setup_method(self):
        """Set up test data."""
        self.config = ClaimifyConfig()
        self.pipeline = ClaimifyPipeline(config=self.config)

        # Create test sentences from the example in on-claim_generation.md
        self.test_sentences = [
            SentenceChunk(
                text='in the else block I get: O argumento do tipo "slice[None, None, None]" não pode ser atribuído ao parâmetro "idx" do tipo "int" na função "__setitem__"',
                source_id="blk_001",
                chunk_id="chunk_001",
                sentence_index=0,
            ),
            SentenceChunk(
                text='"slice[None, None, None]" não pode ser atribuído a "int" PylancereportArgumentType',
                source_id="blk_001",
                chunk_id="chunk_002",
                sentence_index=1,
            ),
        ]

    def test_pipeline_initialization(self):
        """Test pipeline initialization with configuration."""
        # Test with default config
        pipeline = ClaimifyPipeline()
        self.assertIsNotNone(pipeline.config)
        self.assertIsNotNone(pipeline.selection_agent)
        self.assertIsNotNone(pipeline.disambiguation_agent)
        self.assertIsNotNone(pipeline.decomposition_agent)

        # Test with custom config
        custom_config = ClaimifyConfig(
            context_window_p=5, context_window_f=2, selection_model="gpt-4"
        )
        pipeline = ClaimifyPipeline(config=custom_config)
        assert pipeline.config.context_window_p == 5
        assert pipeline.config.context_window_f == 2

    def test_context_window_building(self):
        """Test context window building with different configurations."""
        # Test with default context window (p=3, f=1)
        sentences = [
            SentenceChunk(f"Sentence {i}", "blk_001", f"chunk_{i:03d}", i)
            for i in range(10)
        ]

        # Test context for sentence in middle
        context = self.pipeline._build_context_window(sentences[5], sentences, 5)

        assert len(context.preceding_sentences) == 3
        assert len(context.following_sentences) == 1
        assert context.current_sentence == sentences[5]

        # Test context for sentence at beginning
        context = self.pipeline._build_context_window(sentences[0], sentences, 0)

        assert len(context.preceding_sentences) == 0
        assert len(context.following_sentences) == 1

        # Test context for sentence at end
        context = self.pipeline._build_context_window(
            sentences[-1], sentences, len(sentences) - 1
        )

        assert len(context.preceding_sentences) == 3
        assert len(context.following_sentences) == 0

    def test_single_sentence_processing(self):
        """Test processing of a single sentence through the pipeline."""
        sentence = SentenceChunk(
            text="The system reported an error when processing the request.",
            source_id="blk_001",
            chunk_id="chunk_001",
            sentence_index=0,
        )

        context = ClaimifyContext(current_sentence=sentence)
        result = self.pipeline.process_sentence(context)

        # Check that all stages were processed
        self.assertIsNotNone(result.selection_result)

        if result.selection_result.is_selected:
            # If selected, should have disambiguation and decomposition results
            self.assertIsNotNone(result.disambiguation_result)
            self.assertIsNotNone(result.decomposition_result)
            assert result.was_processed
        else:
            # If not selected, should not have further processing
            assert result.disambiguation_result is None
            assert result.decomposition_result is None
            assert not result.was_processed

        # Should have timing information
        self.assertIsNotNone(result.total_processing_time)

    def test_multiple_sentences_processing(self):
        """Test processing of multiple sentences."""
        results = self.pipeline.process_sentences(self.test_sentences)

        assert len(results) == len(self.test_sentences)

        # Each result should correspond to the correct sentence
        for i, result in enumerate(results):
            assert result.original_chunk == self.test_sentences[i]
            self.assertIsNotNone(result.selection_result)

    def test_empty_sentence_list(self):
        """Test handling of empty sentence list."""
        results = self.pipeline.process_sentences([])

        assert len(results) == 0

    def test_error_handling_in_pipeline(self):
        """Test error handling when processing fails."""
        # Create a sentence that might cause issues
        problematic_sentence = SentenceChunk(
            text="",  # Empty text might cause issues
            source_id="blk_001",
            chunk_id="chunk_001",
            sentence_index=0,
        )

        results = self.pipeline.process_sentences([problematic_sentence])

        assert len(results) == 1
        result = results[0]

        # Should handle gracefully and return a result
        self.assertIsNotNone(result)
        assert result.original_chunk == problematic_sentence

    def test_pipeline_stats_generation(self):
        """Test generation of pipeline statistics."""
        results = self.pipeline.process_sentences(self.test_sentences)
        stats = self.pipeline.get_pipeline_stats(results)

        # Check that stats contain expected fields
        assert "pipeline" in stats
        assert "total_sentences" in stats
        assert "processed_sentences" in stats
        assert "selection_rate" in stats
        assert "total_claims" in stats
        assert "total_sentence_nodes" in stats
        assert "errors" in stats
        assert "timing" in stats

        # Check that values make sense
        assert stats["total_sentences"] == len(self.test_sentences)
        self.assertGreaterEqual(stats["processed_sentences"], 0)
        self.assertLessEqual(stats["processed_sentences"], stats["total_sentences"])
        self.assertGreaterEqual(stats["selection_rate"], 0.0)
        self.assertLessEqual(stats["selection_rate"], 1.0)
        self.assertGreaterEqual(stats["total_claims"], 0)
        self.assertGreaterEqual(stats["total_sentence_nodes"], 0)

    def test_end_to_end_claim_extraction(self):
        """Test end-to-end claim extraction with verifiable content."""
        # Create sentences with clear verifiable content
        verifiable_sentences = [
            SentenceChunk(
                text="The system reported an error with code 500.",
                source_id="blk_002",
                chunk_id="chunk_001",
                sentence_index=0,
            ),
            SentenceChunk(
                text="The error occurred at 10:30 AM on March 15th.",
                source_id="blk_002",
                chunk_id="chunk_002",
                sentence_index=1,
            ),
            SentenceChunk(
                text="It affected 25% of active users.",
                source_id="blk_002",
                chunk_id="chunk_003",
                sentence_index=2,
            ),
        ]

        results = self.pipeline.process_sentences(verifiable_sentences)

        # Should have results for all sentences
        assert len(results) == 3

        # Check for successful processing
        processed_results = [r for r in results if r.was_processed]
        self.assertGreater(len(processed_results), 0)

        # Check for extracted claims or sentence nodes
        total_claims = sum(len(r.final_claims) for r in results)
        total_sentences = sum(len(r.final_sentences) for r in results)

        # Should have extracted some content
        self.assertGreater(total_claims + total_sentences, 0)

    def test_context_window_configuration(self):
        """Test pipeline with different context window configurations."""
        # Test with larger context window
        large_context_config = ClaimifyConfig(context_window_p=5, context_window_f=3)
        pipeline = ClaimifyPipeline(config=large_context_config)

        # Create more sentences to test context window
        sentences = [
            SentenceChunk(f"Sentence {i} with content.", "blk_001", f"chunk_{i:03d}", i)
            for i in range(10)
        ]

        # Test context building with larger window
        context = pipeline._build_context_window(sentences[6], sentences, 6)

        assert len(context.preceding_sentences) == 5
        assert len(context.following_sentences) == 3

    def test_logging_configuration(self):
        """Test pipeline with different logging configurations."""
        # Test with logging disabled
        no_log_config = ClaimifyConfig(
            log_decisions=False, log_transformations=False, log_timing=False
        )
        pipeline = ClaimifyPipeline(config=no_log_config)

        # Should still work without logging
        sentence = SentenceChunk(
            text="Test sentence for logging.",
            source_id="blk_001",
            chunk_id="chunk_001",
            sentence_index=0,
        )

        results = pipeline.process_sentences([sentence])
        assert len(results) == 1

    def test_model_injection(self):
        """Test pipeline with different LLM instances."""
        # Create mock LLMs
        mock_selection_llm = Mock()
        mock_disambiguation_llm = Mock()
        mock_decomposition_llm = Mock()

        # Configure mock responses
        mock_selection_llm.complete.return_value = (
            '{"selected": true, "confidence": 0.9}'
        )
        mock_disambiguation_llm.complete.return_value = "Disambiguated text"
        mock_decomposition_llm.complete.return_value = "Decomposed claim"

        # Create pipeline with injected models
        pipeline = ClaimifyPipeline(
            config=self.config,
            selection_llm=mock_selection_llm,
            disambiguation_llm=mock_disambiguation_llm,
            decomposition_llm=mock_decomposition_llm,
        )

        # Test that the agents have the correct LLMs
        assert pipeline.selection_agent.llm == mock_selection_llm
        assert pipeline.disambiguation_agent.llm == mock_disambiguation_llm
        assert pipeline.decomposition_agent.llm == mock_decomposition_llm

        # Process a sentence (should work even if mocks don't return proper JSON)
        sentence = SentenceChunk(
            text="Test sentence.",
            source_id="blk_001",
            chunk_id="chunk_001",
            sentence_index=0,
        )

        results = pipeline.process_sentences([sentence])
        assert len(results) == 1


class TestClaimifyPipelineIntegration:
    """Integration tests for the Claimify pipeline with realistic scenarios."""

    def test_example_from_documentation(self):
        """Test processing of the example from on-claim_generation.md."""
        config = ClaimifyConfig()
        pipeline = ClaimifyPipeline(config=config)

        # Example sentences from the documentation
        sentences = [
            SentenceChunk(
                text='in the else block I get: O argumento do tipo "slice[None, None, None]" não pode ser atribuído ao parâmetro "idx" do tipo "int" na função "__setitem__"',
                source_id="blk_001",
                chunk_id="chunk_001",
                sentence_index=0,
            ),
            SentenceChunk(
                text='"slice[None, None, None]" não pode ser atribuído a "int" PylancereportArgumentType',
                source_id="blk_001",
                chunk_id="chunk_002",
                sentence_index=1,
            ),
        ]

        results = pipeline.process_sentences(sentences)

        # Should process both sentences
        assert len(results) == 2

        # Both sentences should be selected (contain error information)
        selected_results = [r for r in results if r.was_processed]
        self.assertGreater(len(selected_results), 0)

        # Should extract some claims or create sentence nodes
        total_output = sum(
            len(r.final_claims) + len(r.final_sentences) for r in results
        )
        self.assertGreater(total_output, 0)

    def test_mixed_content_processing(self):
        """Test processing of mixed content (some verifiable, some not)."""
        config = ClaimifyConfig()
        pipeline = ClaimifyPipeline(config=config)

        sentences = [
            # Verifiable technical content
            SentenceChunk(
                text="The system threw a NullPointerException at line 42.",
                source_id="blk_001",
                chunk_id="chunk_001",
                sentence_index=0,
            ),
            # Question (should not be selected)
            SentenceChunk(
                text="What should we do about this?",
                source_id="blk_001",
                chunk_id="chunk_002",
                sentence_index=1,
            ),
            # Short interjection (should not be selected)
            SentenceChunk(
                text="Hmm.", source_id="blk_001", chunk_id="chunk_003", sentence_index=2
            ),
            # Another verifiable statement
            SentenceChunk(
                text="The error rate increased to 15% after the deployment.",
                source_id="blk_001",
                chunk_id="chunk_004",
                sentence_index=3,
            ),
        ]

        results = pipeline.process_sentences(sentences)

        assert len(results) == 4

        # Check selection results
        selected = [r for r in results if r.was_processed]
        not_selected = [r for r in results if not r.was_processed]

        # Should have selected the verifiable content and rejected questions/short text
        self.assertGreater(len(selected), 0)
        self.assertGreater(len(not_selected), 0)

        # Questions and short text should not be selected
        question_result = results[1]  # "What should we do about this?"
        short_result = results[2]  # "Hmm."

        assert not question_result.was_processed
        assert not short_result.was_processed

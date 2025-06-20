"""
Tests for the main Claimify pipeline.
Tests the ClaimifyPipeline orchestrator and end-to-end processing.
"""

import os

# Import the pipeline classes
import sys
from unittest.mock import Mock

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from aclarai_shared.claimify.data_models import (
    ClaimifyConfig,
    ClaimifyContext,
    SentenceChunk,
)
from aclarai_shared.claimify.pipeline import ClaimifyPipeline


class MockLLM:
    """Mock LLM implementation for testing."""

    def __init__(self, response: str = ""):
        self.response = response
        self.calls = []

    def complete(self, prompt: str, **kwargs) -> str:
        self.calls.append((prompt, kwargs))
        return self.response


@pytest.fixture
def config():
    """Test configuration fixture."""
    return ClaimifyConfig()


@pytest.fixture
def mock_selection_llm():
    """Mock LLM for selection that selects content."""
    return MockLLM("The system reported an error with code 500.")


@pytest.fixture
def mock_disambiguation_llm():
    """Mock LLM for disambiguation."""
    return MockLLM("The system reported an error with code 500.")


@pytest.fixture
def mock_decomposition_llm():
    """Mock LLM for decomposition."""
    return MockLLM("The system reported an error with code 500.")


@pytest.fixture
def pipeline_with_llms(
    config, mock_selection_llm, mock_disambiguation_llm, mock_decomposition_llm
):
    """Pipeline with proper LLM mocks."""
    return ClaimifyPipeline(
        config=config,
        selection_llm=mock_selection_llm,
        disambiguation_llm=mock_disambiguation_llm,
        decomposition_llm=mock_decomposition_llm,
    )


@pytest.fixture
def test_sentences():
    """Test sentences fixture."""
    return [
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


class TestClaimifyPipeline:
    """Test ClaimifyPipeline functionality."""

    def test_pipeline_initialization(self):
        """Test pipeline initialization with configuration."""
        # Test with custom config
        custom_config = ClaimifyConfig(
            context_window_p=5, context_window_f=2, selection_model="gpt-4"
        )
        # Create mock LLMs
        mock_llm = MockLLM("test response")
        pipeline = ClaimifyPipeline(
            config=custom_config,
            selection_llm=mock_llm,
            disambiguation_llm=mock_llm,
            decomposition_llm=mock_llm,
        )
        assert pipeline.config.context_window_p == 5
        assert pipeline.config.context_window_f == 2

    def test_context_window_building(self, pipeline_with_llms):
        """Test context window building with different configurations."""
        # Test with default context window (p=3, f=1)
        sentences = [
            SentenceChunk(f"Sentence {i}", "blk_001", f"chunk_{i:03d}", i)
            for i in range(10)
        ]
        # Test context for sentence in middle
        context = pipeline_with_llms._build_context_window(sentences[5], sentences, 5)
        assert len(context.preceding_sentences) == 3
        assert len(context.following_sentences) == 1
        assert context.current_sentence == sentences[5]
        # Test context for sentence at beginning
        context = pipeline_with_llms._build_context_window(sentences[0], sentences, 0)
        assert len(context.preceding_sentences) == 0
        assert len(context.following_sentences) == 1
        # Test context for sentence at end
        context = pipeline_with_llms._build_context_window(
            sentences[-1], sentences, len(sentences) - 1
        )
        assert len(context.preceding_sentences) == 3
        assert len(context.following_sentences) == 0

    def test_single_sentence_processing(self, pipeline_with_llms):
        """Test processing of a single sentence through the pipeline."""
        sentence = SentenceChunk(
            text="The system reported an error when processing the request.",
            source_id="blk_001",
            chunk_id="chunk_001",
            sentence_index=0,
        )
        context = ClaimifyContext(current_sentence=sentence)
        result = pipeline_with_llms.process_sentence(context)
        # Check that all stages were processed
        assert result.selection_result is not None
        if result.selection_result.is_selected:
            # If selected, should have disambiguation and decomposition results
            assert result.disambiguation_result is not None
            assert result.decomposition_result is not None
            assert result.was_processed is True
        else:
            # If not selected, should not have further processing
            assert result.disambiguation_result is None
            assert result.decomposition_result is None
            assert result.was_processed is False
        # Should have timing information
        assert result.total_processing_time is not None

    def test_multiple_sentences_processing(self, pipeline_with_llms, test_sentences):
        """Test processing of multiple sentences."""
        results = pipeline_with_llms.process_sentences(test_sentences)
        assert len(results) == len(test_sentences)
        # Each result should correspond to the correct sentence
        for i, result in enumerate(results):
            assert result.original_chunk == test_sentences[i]
            assert result.selection_result is not None

    def test_empty_sentence_list(self, pipeline_with_llms):
        """Test handling of empty sentence list."""
        results = pipeline_with_llms.process_sentences([])
        assert len(results) == 0

    def test_error_handling_in_pipeline(self, pipeline_with_llms):
        """Test error handling when processing fails."""
        # Create a sentence that might cause issues
        problematic_sentence = SentenceChunk(
            text="",  # Empty text might cause issues
            source_id="blk_001",
            chunk_id="chunk_001",
            sentence_index=0,
        )
        results = pipeline_with_llms.process_sentences([problematic_sentence])
        assert len(results) == 1
        result = results[0]
        # Should handle gracefully and return a result
        assert result is not None
        assert result.original_chunk == problematic_sentence

    def test_pipeline_stats_generation(self, pipeline_with_llms, test_sentences):
        """Test generation of pipeline statistics."""
        results = pipeline_with_llms.process_sentences(test_sentences)
        stats = pipeline_with_llms.get_pipeline_stats(results)
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
        assert stats["total_sentences"] == len(test_sentences)
        assert stats["processed_sentences"] >= 0
        assert stats["processed_sentences"] <= stats["total_sentences"]
        assert stats["selection_rate"] >= 0.0
        assert stats["selection_rate"] <= 1.0
        assert stats["total_claims"] >= 0
        assert stats["total_sentence_nodes"] >= 0

    def test_end_to_end_claim_extraction(self, config):
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
        # Create LLM mocks that will select and process content
        selection_llm = MockLLM(
            '{"selected": true, "confidence": 0.8, "reasoning": "Contains verifiable content"}'
        )
        disambiguation_llm = MockLLM(
            '{"disambiguated_text": "The system reported an error with code 500.", "changes_made": ["No changes needed"], "confidence": 1.0}'
        )
        decomposition_llm = MockLLM(
            '{"claim_candidates": [{"text": "The system reported an error with code 500.", "is_atomic": true, "is_self_contained": true, "is_verifiable": true, "passes_criteria": true, "reasoning": "Valid atomic claim", "node_type": "Claim"}]}'
        )
        pipeline = ClaimifyPipeline(
            config=config,
            selection_llm=selection_llm,
            disambiguation_llm=disambiguation_llm,
            decomposition_llm=decomposition_llm,
        )
        results = pipeline.process_sentences(verifiable_sentences)
        # Should have results for all sentences
        assert len(results) == 3
        # Check for successful processing
        processed_results = [r for r in results if r.was_processed]
        assert len(processed_results) > 0
        # Check for extracted claims or sentence nodes
        total_claims = sum(len(r.final_claims) for r in results)
        total_sentences = sum(len(r.final_sentences) for r in results)
        # Should have extracted some content
        assert total_claims + total_sentences > 0

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

    def test_model_injection(self, config):
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
            config=config,
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

    def test_example_from_documentation(self, config):
        """Test processing of the example from on-claim_generation.md."""
        # Create LLM mocks that will select and process content
        selection_llm = MockLLM(
            '{"selected": true, "confidence": 0.8, "reasoning": "Contains verifiable technical content"}'
        )
        disambiguation_llm = MockLLM(
            '{"disambiguated_text": "Error detected in slice assignment.", "changes_made": ["No changes needed"], "confidence": 1.0}'
        )
        decomposition_llm = MockLLM(
            '{"claim_candidates": [{"text": "Error detected in slice assignment.", "is_atomic": true, "is_self_contained": true, "is_verifiable": true, "passes_criteria": true, "reasoning": "Valid atomic claim", "node_type": "Claim"}]}'
        )
        pipeline = ClaimifyPipeline(
            config=config,
            selection_llm=selection_llm,
            disambiguation_llm=disambiguation_llm,
            decomposition_llm=decomposition_llm,
        )
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
        assert len(selected_results) > 0
        # Should extract some claims or create sentence nodes
        total_output = sum(
            len(r.final_claims) + len(r.final_sentences) for r in results
        )
        assert total_output > 0

    def test_mixed_content_processing(self, config):
        """Test processing of mixed content (some verifiable, some not)."""

        # Create LLM mocks - selection LLM returns content for some and NO_VERIFIABLE_CONTENT for others
        def mock_selection_response(prompt, **_kwargs):
            # Extract the actual target sentence from the prompt
            if 'Target sentence: "' in prompt:
                start_idx = prompt.find('Target sentence: "') + len(
                    'Target sentence: "'
                )
                end_idx = prompt.find('"', start_idx)
                target_sentence = prompt[start_idx:end_idx]
                # Check if the target sentence itself contains verifiable content
                if (
                    "exception" in target_sentence.lower()
                    or "error rate" in target_sentence.lower()
                    or "deployment" in target_sentence.lower()
                ):
                    return '{"selected": true, "confidence": 0.8, "reasoning": "Contains verifiable technical content"}'
                else:
                    return '{"selected": false, "confidence": 0.9, "reasoning": "No verifiable content found"}'
            else:
                return '{"selected": false, "confidence": 0.9, "reasoning": "No verifiable content found"}'

        selection_llm = Mock()
        selection_llm.complete = Mock(side_effect=mock_selection_response)
        disambiguation_llm = MockLLM(
            '{"disambiguated_text": "System error detected.", "changes_made": ["Resolved pronouns"], "confidence": 0.8}'
        )
        decomposition_llm = MockLLM(
            '{"claim_candidates": [{"text": "System error detected.", "is_atomic": true, "is_self_contained": true, "is_verifiable": true, "passes_criteria": true, "reasoning": "Valid atomic claim", "node_type": "Claim"}]}'
        )
        pipeline = ClaimifyPipeline(
            config=config,
            selection_llm=selection_llm,
            disambiguation_llm=disambiguation_llm,
            decomposition_llm=decomposition_llm,
        )
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
        assert len(selected) > 0
        assert len(not_selected) > 0
        # Questions and short text should not be selected
        question_result = results[1]  # "What should we do about this?"
        short_result = results[2]  # "Hmm."
        assert question_result.was_processed is False
        assert short_result.was_processed is False

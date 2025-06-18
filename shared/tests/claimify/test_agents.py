"""
Tests for Claimify pipeline agents.

Tests the Selection, Disambiguation, and Decomposition agents.
"""

import pytest
from unittest.mock import Mock
import sys
import os

# Add path without importing the problematic shared package
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

# Import from claimify directly
from aclarai_shared.claimify.data_models import (
    SentenceChunk,
    ClaimifyContext,
    ClaimifyConfig,
)

from aclarai_shared.claimify.agents import (
    SelectionAgent,
    DisambiguationAgent,
    DecompositionAgent,
)


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
def test_sentence():
    """Test sentence fixture."""
    return SentenceChunk(
        text="The system reported an error when processing the request.",
        source_id="blk_001",
        chunk_id="chunk_001",
        sentence_index=1,
    )


@pytest.fixture
def test_context(test_sentence):
    """Test context fixture."""
    return ClaimifyContext(current_sentence=test_sentence)


class TestSelectionAgent:
    """Test SelectionAgent functionality."""

    def test_llm_selection_verifiable_content(self, config, test_context):
        """Test selection of sentence with verifiable content."""
        json_response = '{"selected": true, "confidence": 0.8, "reasoning": "Contains verifiable technical information"}'
        mock_llm = MockLLM(json_response)
        agent = SelectionAgent(llm=mock_llm, config=config)

        result = agent.process(test_context)

        assert result.is_selected
        assert result.sentence_chunk == test_context.current_sentence
        assert result.confidence == 0.8
        assert "verifiable technical information" in result.reasoning
        assert result.rewritten_text is not None

    def test_llm_selection_no_verifiable_content(self, config):
        """Test rejection of non-verifiable content."""
        json_response = '{"selected": false, "confidence": 0.9, "reasoning": "Question with no verifiable content"}'
        mock_llm = MockLLM(json_response)
        agent = SelectionAgent(llm=mock_llm, config=config)

        question_sentence = SentenceChunk(
            text="What caused the error?",
            source_id="blk_001",
            chunk_id="chunk_002",
            sentence_index=2,
        )
        context = ClaimifyContext(current_sentence=question_sentence)

        result = agent.process(context)

        assert not result.is_selected
        assert result.confidence == 0.9
        assert "Question with no verifiable content" in result.reasoning

    def test_selection_without_llm_fails(self, config, test_context):
        """Test that selection fails without LLM."""
        agent = SelectionAgent(config=config)  # No LLM provided

        result = agent.process(test_context)

        assert not result.is_selected
        assert "LLM is required for Selection agent processing" in result.reasoning

    def test_context_window_building(self, config, test_sentence):
        """Test that context window is properly built."""
        mock_llm = MockLLM("Test response")
        agent = SelectionAgent(llm=mock_llm, config=config)

        preceding = SentenceChunk(
            text="The user submitted a form.",
            source_id="blk_001",
            chunk_id="chunk_000",
            sentence_index=0,
        )

        following = SentenceChunk(
            text="The error was logged to the database.",
            source_id="blk_001",
            chunk_id="chunk_002",
            sentence_index=2,
        )

        context = ClaimifyContext(
            current_sentence=test_sentence,
            preceding_sentences=[preceding],
            following_sentences=[following],
        )

        context_text = agent._build_context_text(context)

        assert "[-1] The user submitted a form." in context_text
        assert (
            "[0] The system reported an error when processing the request. ← TARGET"
            in context_text
        )
        assert "[1] The error was logged to the database." in context_text


class TestDisambiguationAgent:
    """Test DisambiguationAgent functionality."""

    def test_llm_disambiguation_success(self, config):
        """Test successful disambiguation with LLM."""
        json_response = '{"disambiguated_text": "The system reported an error when the system failed.", "changes_made": ["Replaced it with the system", "Replaced this with the system"], "confidence": 0.9}'
        mock_llm = MockLLM(json_response)
        agent = DisambiguationAgent(llm=mock_llm, config=config)

        test_sentence = SentenceChunk(
            text="It reported an error when this failed.",
            source_id="blk_001",
            chunk_id="chunk_001",
            sentence_index=1,
        )
        context = ClaimifyContext(current_sentence=test_sentence)

        result = agent.process(test_sentence, context)

        assert (
            result.disambiguated_text
            == "The system reported an error when the system failed."
        )
        assert len(result.changes_made) == 2
        assert "Replaced it with the system" in result.changes_made
        assert result.confidence == 0.9

    def test_llm_disambiguation_no_changes_needed(self, config):
        """Test sentence that doesn't need disambiguation."""
        original_text = "The system reported an error when the request failed."
        json_response = f'{{"disambiguated_text": "{original_text}", "changes_made": [], "confidence": 1.0}}'
        mock_llm = MockLLM(json_response)
        agent = DisambiguationAgent(llm=mock_llm, config=config)

        clear_sentence = SentenceChunk(
            text=original_text,
            source_id="blk_001",
            chunk_id="chunk_002",
            sentence_index=2,
        )
        context = ClaimifyContext(current_sentence=clear_sentence)

        result = agent.process(clear_sentence, context)

        assert result.disambiguated_text == original_text
        assert len(result.changes_made) == 0
        assert result.confidence == 1.0

    def test_disambiguation_invalid_json_fails(self, config):
        """Test LLM invalid JSON response fails gracefully."""
        mock_llm = MockLLM("INVALID_JSON_RESPONSE")
        agent = DisambiguationAgent(llm=mock_llm, config=config)

        test_sentence = SentenceChunk(
            text="It reported an error when this failed.",
            source_id="blk_001",
            chunk_id="chunk_001",
            sentence_index=1,
        )
        context = ClaimifyContext(current_sentence=test_sentence)

        result = agent.process(test_sentence, context)

        # Should return original text on error
        assert result.disambiguated_text == test_sentence.text
        # Should have error in changes_made
        assert len(result.changes_made) == 1
        assert "Error during processing" in result.changes_made[0]

    def test_disambiguation_without_llm_fails(self, config):
        """Test that disambiguation fails without LLM."""
        agent = DisambiguationAgent(config=config)  # No LLM provided

        test_sentence = SentenceChunk(
            text="It failed.",
            source_id="blk_001",
            chunk_id="chunk_001",
            sentence_index=1,
        )
        context = ClaimifyContext(current_sentence=test_sentence)

        result = agent.process(test_sentence, context)

        assert (
            "LLM is required for Disambiguation agent processing"
            in result.changes_made[0]
        )


class TestDecompositionAgent:
    """Test DecompositionAgent functionality."""

    def test_llm_decomposition_single_claim(self, config):
        """Test processing of a simple atomic claim."""
        json_response = """{"claim_candidates": [{"text": "The system reported an error.", "is_atomic": true, "is_self_contained": true, "is_verifiable": true, "passes_criteria": true, "confidence": 0.95, "reasoning": "Single atomic verifiable fact", "node_type": "Claim"}]}"""
        mock_llm = MockLLM(json_response)
        agent = DecompositionAgent(llm=mock_llm, config=config)

        test_sentence = SentenceChunk(
            text="The system reported an error.",
            source_id="blk_001",
            chunk_id="chunk_001",
            sentence_index=1,
        )

        text = "The system reported an error."
        result = agent.process(text, test_sentence)

        assert len(result.claim_candidates) == 1
        claim = result.claim_candidates[0]
        assert claim.text == text
        assert claim.is_atomic
        assert claim.is_self_contained
        assert claim.is_verifiable
        assert claim.confidence == 0.95  # From LLM response

    def test_llm_decomposition_multiple_claims(self, config):
        """Test splitting of compound sentences and JSON parsing."""
        json_response = """{"claim_candidates": [{"text": "The system reported an error.", "is_atomic": true, "is_self_contained": true, "is_verifiable": true, "passes_criteria": true, "confidence": 0.92, "reasoning": "First atomic claim", "node_type": "Claim"}, {"text": "The user was notified.", "is_atomic": true, "is_self_contained": true, "is_verifiable": true, "passes_criteria": true, "confidence": 0.88, "reasoning": "Second atomic claim", "node_type": "Claim"}]}"""
        mock_llm = MockLLM(json_response)
        agent = DecompositionAgent(llm=mock_llm, config=config)

        test_sentence = SentenceChunk(
            text="compound sentence",
            source_id="blk_001",
            chunk_id="chunk_001",
            sentence_index=1,
        )

        text = "The system reported an error and the user was notified."
        result = agent.process(text, test_sentence)

        # Verify JSON parsing worked correctly
        assert len(result.claim_candidates) == 2

        # Verify quality flags are correctly parsed from JSON
        for claim in result.claim_candidates:
            assert claim.is_atomic is True
            assert claim.is_self_contained is True
            assert claim.is_verifiable is True

        # Verify specific claim content
        claim_texts = [claim.text for claim in result.claim_candidates]
        assert "The system reported an error." in claim_texts
        assert "The user was notified." in claim_texts

    def test_claim_candidate_quality_flags_parsing(self, config):
        """Test that quality flags are correctly parsed from LLM JSON output."""
        # JSON with mixed quality flags
        json_response = """{"claim_candidates": [
            {
                "text": "Valid atomic claim.",
                "is_atomic": true,
                "is_self_contained": true,
                "is_verifiable": true,
                "passes_criteria": true,
                "confidence": 0.93,
                "reasoning": "Meets all criteria",
                "node_type": "Claim"
            },
            {
                "text": "This is not atomic and has multiple facts.",
                "is_atomic": false,
                "is_self_contained": true,
                "is_verifiable": true,
                "passes_criteria": false,
                "confidence": 0.25,
                "reasoning": "Not atomic - compound statement",
                "node_type": "Sentence"
            }
        ]}"""

        # Set a low confidence threshold to include all candidates
        config = ClaimifyConfig(decomposition_confidence_threshold=0.1)

        mock_llm = MockLLM(json_response)
        agent = DecompositionAgent(llm=mock_llm, config=config)

        test_sentence = SentenceChunk(
            text="test sentence",
            source_id="blk_001",
            chunk_id="chunk_001",
            sentence_index=1,
        )

        result = agent.process("Test input text.", test_sentence)

        assert len(result.claim_candidates) == 2

        # First claim should pass all criteria
        valid_claim = result.claim_candidates[0]
        assert valid_claim.is_atomic is True
        assert valid_claim.is_self_contained is True
        assert valid_claim.is_verifiable is True
        assert valid_claim.text == "Valid atomic claim."

        # Second claim should fail atomicity
        invalid_claim = result.claim_candidates[1]
        assert invalid_claim.is_atomic is False
        assert invalid_claim.is_self_contained is True
        assert invalid_claim.is_verifiable is True
        assert invalid_claim.text == "This is not atomic and has multiple facts."

    def test_llm_decomposition_no_valid_claims(self, config):
        """Test when LLM finds no valid claims."""
        json_response = '{"claim_candidates": []}'
        mock_llm = MockLLM(json_response)
        agent = DecompositionAgent(llm=mock_llm, config=config)

        test_sentence = SentenceChunk(
            text="test",
            source_id="blk_001",
            chunk_id="chunk_001",
            sentence_index=1,
        )

        text = "It caused an error in the system."
        result = agent.process(text, test_sentence)

        assert len(result.claim_candidates) == 0

    def test_decomposition_without_llm_fails(self, config):
        """Test that decomposition fails without LLM."""
        agent = DecompositionAgent(config=config)  # No LLM provided

        test_sentence = SentenceChunk(
            text="test sentence",
            source_id="blk_001",
            chunk_id="chunk_001",
            sentence_index=1,
        )

        result = agent.process("test text", test_sentence)

        assert len(result.claim_candidates) == 0

    def test_decomposition_confidence_fallback_calculation(self, config):
        """Test confidence fallback calculation when LLM doesn't provide confidence."""
        # JSON response without confidence field - should trigger fallback calculation
        json_response = """{"claim_candidates": [
            {
                "text": "Perfect claim meeting all criteria.",
                "is_atomic": true,
                "is_self_contained": true,
                "is_verifiable": true,
                "passes_criteria": true,
                "reasoning": "Meets all criteria - no confidence provided",
                "node_type": "Claim"
            },
            {
                "text": "Partial claim meeting some criteria.",
                "is_atomic": true,
                "is_self_contained": true,
                "is_verifiable": false,
                "passes_criteria": false,
                "reasoning": "Meets 2 of 3 criteria - no confidence provided",
                "node_type": "Sentence"
            },
            {
                "text": "Poor claim meeting few criteria.",
                "is_atomic": false,
                "is_self_contained": false,
                "is_verifiable": false,
                "passes_criteria": false,
                "reasoning": "Meets 0 of 3 criteria - no confidence provided",
                "node_type": "Sentence"
            }
        ]}"""

        # Set a low confidence threshold to include all candidates
        config = ClaimifyConfig(decomposition_confidence_threshold=0.1)

        mock_llm = MockLLM(json_response)
        agent = DecompositionAgent(llm=mock_llm, config=config)

        test_sentence = SentenceChunk(
            text="test sentence",
            source_id="blk_001",
            chunk_id="chunk_001",
            sentence_index=1,
        )

        result = agent.process("Test input text.", test_sentence)

        assert len(result.claim_candidates) == 3

        # Test fallback confidence calculation
        # Perfect claim (all criteria met): should get 0.9
        perfect_claim = result.claim_candidates[0]
        assert perfect_claim.confidence == 0.9
        assert perfect_claim.text == "Perfect claim meeting all criteria."

        # Partial claim (2 of 3 criteria): should get 0.6
        partial_claim = result.claim_candidates[1]
        assert partial_claim.confidence == 0.6
        assert partial_claim.text == "Partial claim meeting some criteria."

        # Poor claim (0 of 3 criteria): should get 0.3
        poor_claim = result.claim_candidates[2]
        assert poor_claim.confidence == 0.3
        assert poor_claim.text == "Poor claim meeting few criteria."


class TestAgentErrorHandling:
    """Test error handling in agents."""

    def test_selection_agent_error_handling(self, config):
        """Test SelectionAgent error handling."""
        # Create agent with mock LLM that raises exception
        mock_llm = Mock()
        mock_llm.complete.side_effect = Exception("LLM error")

        agent = SelectionAgent(llm=mock_llm, config=config)

        test_sentence = SentenceChunk(
            text="Test sentence.",
            source_id="blk_001",
            chunk_id="chunk_001",
            sentence_index=1,
        )
        context = ClaimifyContext(current_sentence=test_sentence)

        # Should handle error gracefully
        result = agent.process(context)

        assert result is not None
        assert result.sentence_chunk == test_sentence
        assert not result.is_selected  # Should fail gracefully
        assert "Error during processing" in result.reasoning

    def test_disambiguation_agent_error_handling(self, config):
        """Test DisambiguationAgent error handling."""
        mock_llm = Mock()
        mock_llm.complete.side_effect = Exception("LLM error")

        agent = DisambiguationAgent(llm=mock_llm, config=config)

        test_sentence = SentenceChunk(
            text="Test sentence.",
            source_id="blk_001",
            chunk_id="chunk_001",
            sentence_index=1,
        )
        context = ClaimifyContext(current_sentence=test_sentence)

        # Should handle error gracefully
        result = agent.process(test_sentence, context)

        assert result is not None
        assert result.original_sentence == test_sentence
        assert (
            result.disambiguated_text == test_sentence.text
        )  # Returns original on error

    def test_decomposition_agent_error_handling(self, config):
        """Test DecompositionAgent error handling."""
        mock_llm = Mock()
        mock_llm.complete.side_effect = Exception("LLM error")

        agent = DecompositionAgent(llm=mock_llm, config=config)

        test_sentence = SentenceChunk(
            text="Test sentence.",
            source_id="blk_001",
            chunk_id="chunk_001",
            sentence_index=1,
        )

        # Should handle error gracefully
        result = agent.process("Test text", test_sentence)

        assert result is not None
        assert result.original_text == "Test text"
        assert len(result.claim_candidates) == 0  # No claims on error


class TestAgentConfidenceThresholds:
    """Test confidence threshold enforcement in all agents."""

    def test_selection_agent_confidence_threshold_rejection(self):
        """Test SelectionAgent rejects selections below confidence threshold."""
        # Set a high confidence threshold
        config = ClaimifyConfig(selection_confidence_threshold=0.8)

        # LLM returns selection with low confidence
        json_response = '{"selected": true, "confidence": 0.3, "reasoning": "Contains some verifiable content"}'
        mock_llm = MockLLM(json_response)
        agent = SelectionAgent(llm=mock_llm, config=config)

        test_sentence = SentenceChunk(
            text="The system might have failed.",
            source_id="blk_001",
            chunk_id="chunk_001",
            sentence_index=1,
        )
        context = ClaimifyContext(current_sentence=test_sentence)

        result = agent.process(context)

        # Should be rejected due to low confidence
        assert not result.is_selected
        assert result.confidence == 0.3  # Original confidence preserved
        assert "below threshold" in result.reasoning

    def test_selection_agent_confidence_threshold_acceptance(self):
        """Test SelectionAgent accepts selections above confidence threshold."""
        # Set a moderate confidence threshold
        config = ClaimifyConfig(selection_confidence_threshold=0.5)

        # LLM returns selection with high confidence
        json_response = '{"selected": true, "confidence": 0.9, "reasoning": "Contains clear verifiable content"}'
        mock_llm = MockLLM(json_response)
        agent = SelectionAgent(llm=mock_llm, config=config)

        test_sentence = SentenceChunk(
            text="The system failed at 10:30 AM.",
            source_id="blk_001",
            chunk_id="chunk_001",
            sentence_index=1,
        )
        context = ClaimifyContext(current_sentence=test_sentence)

        result = agent.process(context)

        # Should be accepted due to high confidence
        assert result.is_selected
        assert result.confidence == 0.9

    def test_disambiguation_agent_confidence_threshold_fallback(self):
        """Test DisambiguationAgent falls back to original text when confidence is low."""
        # Set a high confidence threshold
        config = ClaimifyConfig(disambiguation_confidence_threshold=0.7)

        # LLM returns disambiguation with low confidence
        json_response = '{"disambiguated_text": "The uncertain system failed.", "changes_made": ["Uncertain replacement"], "confidence": 0.4}'
        mock_llm = MockLLM(json_response)
        agent = DisambiguationAgent(llm=mock_llm, config=config)

        test_sentence = SentenceChunk(
            text="It failed.",
            source_id="blk_001",
            chunk_id="chunk_001",
            sentence_index=1,
        )
        context = ClaimifyContext(current_sentence=test_sentence)

        result = agent.process(test_sentence, context)

        # Should fall back to original text due to low confidence
        assert result.disambiguated_text == "It failed."  # Original text
        assert result.confidence == 0.4  # Original confidence preserved
        assert "below threshold" in result.changes_made[0]

    def test_decomposition_agent_confidence_threshold_filtering(self):
        """Test DecompositionAgent filters out low-confidence claims."""
        # Set a high confidence threshold
        config = ClaimifyConfig(decomposition_confidence_threshold=0.7)

        # LLM returns mix of high and low confidence claims
        json_response = """{"claim_candidates": [
            {"text": "High quality claim", "is_atomic": true, "is_self_contained": true, "is_verifiable": true, "passes_criteria": true, "confidence": 0.95, "reasoning": "Excellent claim"},
            {"text": "Low quality claim", "is_atomic": false, "is_self_contained": false, "is_verifiable": false, "passes_criteria": false, "confidence": 0.2, "reasoning": "Poor claim"}
        ]}"""
        mock_llm = MockLLM(json_response)
        agent = DecompositionAgent(llm=mock_llm, config=config)

        result = agent.process("Test text", None)

        # Should only include high-confidence claim (0.9) and exclude low-confidence claim (0.3)
        assert len(result.claim_candidates) == 1
        assert result.claim_candidates[0].text == "High quality claim"
        assert result.claim_candidates[0].confidence == 0.95

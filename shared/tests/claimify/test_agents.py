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
from clarifai_shared.claimify.data_models import (
    SentenceChunk,
    ClaimifyContext,
    ClaimifyConfig,
    NodeType,
)

from clarifai_shared.claimify.agents import (
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
        mock_llm = MockLLM("The system reported an error when processing the request.")
        agent = SelectionAgent(llm=mock_llm, config=config)
        
        result = agent.process(test_context)

        assert result.is_selected
        assert result.sentence_chunk == test_context.current_sentence
        assert result.reasoning is not None
        assert result.rewritten_text is not None

    def test_llm_selection_no_verifiable_content(self, config):
        """Test rejection of non-verifiable content."""
        mock_llm = MockLLM("NO_VERIFIABLE_CONTENT")
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
        assert "No verifiable content found" in result.reasoning

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
        assert "[0] The system reported an error when processing the request. ← TARGET" in context_text
        assert "[1] The error was logged to the database." in context_text


class TestDisambiguationAgent:
    """Test DisambiguationAgent functionality."""

    def test_llm_disambiguation_success(self, config):
        """Test successful disambiguation with LLM."""
        mock_llm = MockLLM("The system reported an error when the system failed.")
        agent = DisambiguationAgent(llm=mock_llm, config=config)
        
        test_sentence = SentenceChunk(
            text="It reported an error when this failed.",
            source_id="blk_001",
            chunk_id="chunk_001",
            sentence_index=1,
        )
        context = ClaimifyContext(current_sentence=test_sentence)

        result = agent.process(test_sentence, context)

        assert result.disambiguated_text != test_sentence.text
        assert len(result.changes_made) > 0
        assert "Resolved pronouns and ambiguous references" in result.changes_made

    def test_llm_disambiguation_no_changes_needed(self, config):
        """Test sentence that doesn't need disambiguation."""
        # LLM returns the same text, indicating no changes needed
        original_text = "The system reported an error when the request failed."
        mock_llm = MockLLM(original_text)
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

    def test_disambiguation_cannot_resolve(self, config):
        """Test LLM cannot resolve ambiguities."""
        mock_llm = MockLLM("CANNOT_DISAMBIGUATE")
        agent = DisambiguationAgent(llm=mock_llm, config=config)
        
        test_sentence = SentenceChunk(
            text="It reported an error when this failed.",
            source_id="blk_001",
            chunk_id="chunk_001",
            sentence_index=1,
        )
        context = ClaimifyContext(current_sentence=test_sentence)

        result = agent.process(test_sentence, context)

        assert result.disambiguated_text == test_sentence.text  # Original kept
        assert "Could not resolve ambiguities" in result.changes_made
        assert result.confidence == 0.0

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
        
        assert "LLM is required for Disambiguation agent processing" in result.changes_made[0]


class TestDecompositionAgent:
    """Test DecompositionAgent functionality."""

    def test_llm_decomposition_single_claim(self, config):
        """Test processing of a simple atomic claim."""
        mock_llm = MockLLM("The system reported an error.")
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
        assert claim.passes_criteria
        assert claim.node_type == NodeType.CLAIM

    def test_llm_decomposition_multiple_claims(self, config):
        """Test splitting of compound sentences."""
        mock_llm = MockLLM("The system reported an error.\nThe user was notified.")
        agent = DecompositionAgent(llm=mock_llm, config=config)
        
        test_sentence = SentenceChunk(
            text="compound sentence",
            source_id="blk_001", 
            chunk_id="chunk_001",
            sentence_index=1,
        )
        
        text = "The system reported an error and the user was notified."
        result = agent.process(text, test_sentence)

        # Should split into multiple candidates
        assert len(result.claim_candidates) >= 1
        
        # Check that we got some claims
        claim_texts = [claim.text for claim in result.claim_candidates]
        assert len(claim_texts) > 0

    def test_llm_decomposition_no_valid_claims(self, config):
        """Test when LLM finds no valid claims."""
        mock_llm = MockLLM("NO_VALID_CLAIMS")
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
        assert result.disambiguated_text == test_sentence.text  # Returns original on error

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

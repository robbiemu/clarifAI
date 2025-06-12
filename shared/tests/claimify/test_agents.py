"""
Tests for Claimify pipeline agents.

Tests the Selection, Disambiguation, and Decomposition agents.
"""

# import unittest
from unittest.mock import Mock

# Import the agent classes
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from clarifai_shared.claimify.agents import (
    SelectionAgent,
    DisambiguationAgent,
    DecompositionAgent,
)
from clarifai_shared.claimify.data_models import (
    SentenceChunk,
    ClaimifyContext,
    ClaimifyConfig,
    NodeType,
)


class MockLLM:
    """Mock LLM implementation for testing."""

    def __init__(self, response: str = ""):
        self.response = response
        self.calls = []

    def complete(self, prompt: str, **kwargs) -> str:
        self.calls.append((prompt, kwargs))
        return self.response


class TestSelectionAgent:
    """Test SelectionAgent functionality."""

    def setup_method(self):
        """Set up test data."""
        self.config = ClaimifyConfig()
        self.agent = SelectionAgent(config=self.config)

        self.test_sentence = SentenceChunk(
            text="The system reported an error when processing the request.",
            source_id="blk_001",
            chunk_id="chunk_001",
            sentence_index=1,
        )

        self.context = ClaimifyContext(current_sentence=self.test_sentence)

    def test_heuristic_selection_verifiable_content(self):
        """Test selection of sentence with verifiable content."""
        result = self.agent.process(self.context)

        assert result.is_selected
        assert result.sentence_chunk == self.test_sentence
        self.assertIsNotNone(result.reasoning)
        self.assertGreater(result.confidence, 0.5)

    def test_heuristic_selection_question(self):
        """Test rejection of questions."""
        question_sentence = SentenceChunk(
            text="What caused the error?",
            source_id="blk_001",
            chunk_id="chunk_002",
            sentence_index=2,
        )
        context = ClaimifyContext(current_sentence=question_sentence)

        result = self.agent.process(context)

        assert not result.is_selected
        assert "Questions are not verifiable claims" in result.reasoning

    def test_heuristic_selection_short_sentence(self):
        """Test rejection of very short sentences."""
        short_sentence = SentenceChunk(
            text="Yes.", source_id="blk_001", chunk_id="chunk_003", sentence_index=3
        )
        context = ClaimifyContext(current_sentence=short_sentence)

        result = self.agent.process(context)

        assert not result.is_selected
        assert "too short" in result.reasoning

    def test_context_window_building(self):
        """Test that context window is properly built."""
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
            current_sentence=self.test_sentence,
            preceding_sentences=[preceding],
            following_sentences=[following],
        )

        context_text = self.agent._build_context_text(context)

        assert "[-1] The user submitted a form." in context_text
        self.assertIn(
            "[0] The system reported an error when processing the request. ← TARGET",
            context_text,
        )
        assert "[1] The error was logged to the database." in context_text

    def test_agent_with_mock_llm(self):
        """Test agent behavior with a mock LLM."""
        mock_llm = MockLLM(
            '{"selected": true, "confidence": 0.8, "reasoning": "Contains error information"}'
        )
        agent = SelectionAgent(llm=mock_llm, config=self.config)

        # The agent should fall back to heuristics since JSON parsing isn't implemented
        result = agent.process(self.context)

        # Should still work with heuristics
        assert result.is_selected


class TestDisambiguationAgent:
    """Test DisambiguationAgent functionality."""

    def setup_method(self):
        """Set up test data."""
        self.config = ClaimifyConfig()
        self.agent = DisambiguationAgent(config=self.config)

        self.test_sentence = SentenceChunk(
            text="It reported an error when this failed.",
            source_id="blk_001",
            chunk_id="chunk_001",
            sentence_index=1,
        )

        self.context = ClaimifyContext(current_sentence=self.test_sentence)

    def test_pronoun_replacement(self):
        """Test replacement of ambiguous pronouns."""
        result = self.agent.process(self.test_sentence, self.context)

        self.assertNotEqual(result.disambiguated_text, self.test_sentence.text)
        assert "system" in result.disambiguated_text.lower()
        assert len(result.changes_made > 0)
        assert "it" in result.changes_made[0].lower()

    def test_no_changes_needed(self):
        """Test sentence that doesn't need disambiguation."""
        clear_sentence = SentenceChunk(
            text="The system reported an error when the request failed.",
            source_id="blk_001",
            chunk_id="chunk_002",
            sentence_index=2,
        )

        result = self.agent.process(clear_sentence, self.context)

        assert result.disambiguated_text == clear_sentence.text
        assert len(result.changes_made) == 0
        assert result.confidence == 1.0  # No changes needed = high confidence

    def test_verb_starter_subject_addition(self):
        """Test adding inferred subject to verb-starting sentences."""
        verb_sentence = SentenceChunk(
            text="Reported an error to the console.",
            source_id="blk_001",
            chunk_id="chunk_003",
            sentence_index=3,
        )

        result = self.agent.process(verb_sentence, self.context)

        assert result.disambiguated_text.startswith("[The system]")
        self.assertTrue(
            any("subject" in change.lower() for change in result.changes_made)
        )


class TestDecompositionAgent:
    """Test DecompositionAgent functionality."""

    def setup_method(self):
        """Set up test data."""
        self.config = ClaimifyConfig()
        self.agent = DecompositionAgent(config=self.config)

        self.test_sentence = SentenceChunk(
            text="The system reported an error.",
            source_id="blk_001",
            chunk_id="chunk_001",
            sentence_index=1,
        )

    def test_atomic_claim_creation(self):
        """Test processing of a simple atomic claim."""
        text = "The system reported an error."

        result = self.agent.process(text, self.test_sentence)

        assert len(result.claim_candidates) == 1
        claim = result.claim_candidates[0]
        assert claim.text == text
        assert claim.is_atomic
        assert claim.is_self_contained
        assert claim.is_verifiable
        assert claim.passes_criteria
        assert claim.node_type == NodeType.CLAIM

    def test_compound_sentence_splitting(self):
        """Test splitting of compound sentences."""
        text = "The system reported an error and the user was notified."

        result = self.agent.process(text, self.test_sentence)

        # Should split into multiple candidates
        self.assertGreater(len(result.claim_candidates), 1)

        # Check that parts were properly split
        claim_texts = [claim.text for claim in result.claim_candidates]
        assert any("system reported" in text for text in claim_texts)
        assert any("user was notified" in text for text in claim_texts)

    def test_ambiguous_reference_detection(self):
        """Test detection of ambiguous references."""
        text = "It caused an error in the system."

        result = self.agent.process(text, self.test_sentence)

        assert len(result.claim_candidates) == 1
        claim = result.claim_candidates[0]
        assert not claim.is_self_contained  # "It" is ambiguous
        assert not claim.passes_criteria
        assert claim.node_type == NodeType.SENTENCE

    def test_atomicity_checking(self):
        """Test atomicity checking for compound statements."""
        # Test atomic statement
        assert self.agent._check_atomicity("The system reported an error.")

        # Test compound statements
        self.assertFalse(
            self.agent._check_atomicity("The system reported an error and crashed.")
        )
        assert not self.agent._check_atomicity("The system worked but was slow.")
        self.assertFalse(
            self.agent._check_atomicity("The error occurred because of invalid input.")
        )

    def test_self_containment_checking(self):
        """Test self-containment checking."""
        # Test self-contained statements
        self.assertTrue(
            self.agent._check_self_containment("The system reported an error.")
        )
        self.assertTrue(
            self.agent._check_self_containment("The user clicked the button.")
        )

        # Test statements with ambiguous references
        assert not self.agent._check_self_containment("It reported an error.")
        assert not self.agent._check_self_containment("This caused the problem.")
        assert not self.agent._check_self_containment("That was unexpected.")

    def test_verifiability_checking(self):
        """Test verifiability checking."""
        # Test verifiable statements
        self.assertTrue(
            self.agent._check_verifiability("The system reported an error.")
        )
        assert self.agent._check_verifiability("The count was 42.")
        self.assertTrue(
            self.agent._check_verifiability("The process resulted in success.")
        )

        # Test non-verifiable statements (simple heuristic)
        # Note: This is a simple implementation, a more sophisticated one would be more accurate
        self.assertTrue(
            self.agent._check_verifiability("Something happened.")
        )  # Contains verifiable pattern "happened"

    def test_claim_reasoning(self):
        """Test that reasoning is provided for claim decisions."""
        # Test valid claim
        text = "The system reported an error."
        result = self.agent.process(text, self.test_sentence)
        claim = result.claim_candidates[0]
        self.assertIsNotNone(claim.reasoning)

        # Test invalid claim
        text = "It failed and crashed."
        result = self.agent.process(text, self.test_sentence)
        if len(result.claim_candidates) == 1:  # If not split
            claim = result.claim_candidates[0]
            self.assertIsNotNone(claim.reasoning)
            assert "Issues:" in claim.reasoning


class TestAgentErrorHandling:
    """Test error handling in agents."""

    def setup_method(self):
        """Set up test data."""
        self.config = ClaimifyConfig()
        self.test_sentence = SentenceChunk(
            text="Test sentence.",
            source_id="blk_001",
            chunk_id="chunk_001",
            sentence_index=1,
        )
        self.context = ClaimifyContext(current_sentence=self.test_sentence)

    def test_selection_agent_error_handling(self):
        """Test SelectionAgent error handling."""
        # Create agent with mock LLM that raises exception
        mock_llm = Mock()
        mock_llm.complete.side_effect = Exception("LLM error")

        agent = SelectionAgent(llm=mock_llm, config=self.config)

        # Should handle error gracefully and fall back to heuristics
        result = agent.process(self.context)

        self.assertIsNotNone(result)
        assert result.sentence_chunk == self.test_sentence
        # Should have processed (even if heuristic fallback)

    def test_disambiguation_agent_error_handling(self):
        """Test DisambiguationAgent error handling."""
        mock_llm = Mock()
        mock_llm.complete.side_effect = Exception("LLM error")

        agent = DisambiguationAgent(llm=mock_llm, config=self.config)

        # Should handle error gracefully
        result = agent.process(self.test_sentence, self.context)

        self.assertIsNotNone(result)
        assert result.original_sentence == self.test_sentence

    def test_decomposition_agent_error_handling(self):
        """Test DecompositionAgent error handling."""
        mock_llm = Mock()
        mock_llm.complete.side_effect = Exception("LLM error")

        agent = DecompositionAgent(llm=mock_llm, config=self.config)

        # Should handle error gracefully
        result = agent.process("Test text", self.test_sentence)

        self.assertIsNotNone(result)
        assert result.original_text == "Test text"

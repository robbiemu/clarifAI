"""
Tests for Claimify pipeline data models.
Tests the core data structures used throughout the Claimify pipeline.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from aclarai_shared.claimify.data_models import (
    ClaimCandidate,
    ClaimifyConfig,
    ClaimifyContext,
    ClaimifyResult,
    DecompositionResult,
    DisambiguationResult,
    NodeType,
    SelectionResult,
    SentenceChunk,
)


def test_sentence_chunk_creation():
    """Test basic SentenceChunk creation."""
    chunk = SentenceChunk(
        text="This is a test sentence.",
        source_id="blk_001",
        chunk_id="chunk_001",
        sentence_index=0,
    )
    assert chunk.text == "This is a test sentence."
    assert chunk.source_id == "blk_001"
    assert chunk.chunk_id == "chunk_001"
    assert chunk.sentence_index == 0


@pytest.fixture
def current_sentence():
    """Fixture for current sentence."""
    return SentenceChunk(
        text="This is the current sentence.",
        source_id="blk_001",
        chunk_id="chunk_002",
        sentence_index=1,
    )


@pytest.fixture
def preceding_sentence():
    """Fixture for preceding sentence."""
    return SentenceChunk(
        text="This is a preceding sentence.",
        source_id="blk_001",
        chunk_id="chunk_001",
        sentence_index=0,
    )


@pytest.fixture
def following_sentence():
    """Fixture for following sentence."""
    return SentenceChunk(
        text="This is a following sentence.",
        source_id="blk_001",
        chunk_id="chunk_003",
        sentence_index=2,
    )


def test_context_creation(current_sentence, preceding_sentence, following_sentence):
    """Test ClaimifyContext creation."""
    context = ClaimifyContext(
        current_sentence=current_sentence,
        preceding_sentences=[preceding_sentence],
        following_sentences=[following_sentence],
    )
    assert context.current_sentence == current_sentence
    assert len(context.preceding_sentences) == 1
    assert len(context.following_sentences) == 1
    assert context.context_window_size == (1, 1)


def test_empty_context(current_sentence):
    """Test context with no surrounding sentences."""
    context = ClaimifyContext(current_sentence=current_sentence)
    assert len(context.preceding_sentences) == 0
    assert len(context.following_sentences) == 0
    assert context.context_window_size == (0, 0)


def test_valid_claim_candidate():
    """Test a claim candidate that passes all criteria."""
    candidate = ClaimCandidate(
        text="The system reported an error.",
        is_atomic=True,
        is_self_contained=True,
        is_verifiable=True,
        confidence=0.9,
    )
    assert candidate.passes_criteria is True
    assert candidate.node_type == NodeType.CLAIM


def test_invalid_claim_candidate():
    """Test a claim candidate that fails criteria."""
    candidate = ClaimCandidate(
        text="It caused an error and the user was confused.",
        is_atomic=False,  # Not atomic due to compound structure
        is_self_contained=False,  # "It" is ambiguous
        is_verifiable=True,
        confidence=0.6,
    )
    assert candidate.passes_criteria is False
    assert candidate.node_type == NodeType.SENTENCE


def test_partial_failure():
    """Test a candidate that fails some but not all criteria."""
    candidate = ClaimCandidate(
        text="The error occurred.",
        is_atomic=True,
        is_self_contained=True,
        is_verifiable=False,  # Not specific enough to be verifiable
        confidence=0.7,
    )
    assert candidate.passes_criteria is False
    assert candidate.node_type == NodeType.SENTENCE


def test_decomposition_result_filtering():
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
    assert len(result.valid_claims) == 1
    assert len(result.sentence_nodes) == 1
    assert result.valid_claims[0].text == "The system reported an error."
    assert result.sentence_nodes[0].text == "It was problematic."


@pytest.fixture
def test_sentence():
    """Fixture for test sentence."""
    return SentenceChunk(
        text="The user received an error from the system.",
        source_id="blk_001",
        chunk_id="chunk_001",
        sentence_index=0,
    )


@pytest.fixture
def test_context(test_sentence):
    """Fixture for test context."""
    return ClaimifyContext(current_sentence=test_sentence)


def test_unprocessed_result(test_sentence, test_context):
    """Test result for sentence that was not selected."""
    selection_result = SelectionResult(
        sentence_chunk=test_sentence,
        is_selected=False,
        reasoning="No verifiable content found",
    )
    result = ClaimifyResult(
        original_chunk=test_sentence,
        context=test_context,
        selection_result=selection_result,
    )
    assert result.was_processed is False
    assert len(result.final_claims) == 0
    assert len(result.final_sentences) == 0


def test_processed_result_with_claims(test_sentence, test_context):
    """Test result for sentence that produced valid claims."""
    selection_result = SelectionResult(
        sentence_chunk=test_sentence,
        is_selected=True,
        reasoning="Contains verifiable error information",
    )
    disambiguation_result = DisambiguationResult(
        original_sentence=test_sentence,
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
        original_chunk=test_sentence,
        context=test_context,
        selection_result=selection_result,
        disambiguation_result=disambiguation_result,
        decomposition_result=decomposition_result,
    )
    assert result.was_processed is True
    assert len(result.final_claims) == 1
    assert len(result.final_sentences) == 0
    assert result.final_claims[0].text == "The user received an error from the system."


def test_default_config():
    """Test default configuration values."""
    config = ClaimifyConfig()
    assert config.context_window_p == 3
    assert config.context_window_f == 1
    assert config.default_model == "gpt-3.5-turbo"
    assert config.selection_model is None
    assert config.max_retries == 3
    assert config.temperature == 0.1


def test_custom_config():
    """Test custom configuration values."""
    config = ClaimifyConfig(
        context_window_p=5,
        context_window_f=2,
        selection_model="gpt-4",
        disambiguation_model="claude-3-opus",
        decomposition_model="gpt-4",
        temperature=0.2,
    )
    assert config.context_window_p == 5
    assert config.context_window_f == 2
    assert config.get_model_for_stage("selection") == "gpt-4"
    assert config.get_model_for_stage("disambiguation") == "claude-3-opus"
    assert config.get_model_for_stage("decomposition") == "gpt-4"
    assert config.temperature == 0.2


def test_model_fallback():
    """Test fallback to default model when stage model not configured."""
    config = ClaimifyConfig(
        default_model="custom-model",
        selection_model="gpt-4",  # Only selection model configured
    )
    assert config.get_model_for_stage("selection") == "gpt-4"
    assert config.get_model_for_stage("disambiguation") == "custom-model"
    assert config.get_model_for_stage("decomposition") == "custom-model"

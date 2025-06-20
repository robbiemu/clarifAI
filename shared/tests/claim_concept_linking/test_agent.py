"""Tests for the ClaimConceptLinkerAgent."""

from unittest.mock import Mock, patch

import pytest
from aclarai_shared.claim_concept_linking.agent import ClaimConceptLinkerAgent
from aclarai_shared.claim_concept_linking.models import (
    ClaimConceptPair,
)


class TestClaimConceptLinkerAgent:
    """Test the ClaimConceptLinkerAgent class."""

    @patch("aclarai_shared.claim_concept_linking.agent.load_config")
    @patch("aclarai_shared.claim_concept_linking.agent.OpenAI")
    def test_init_with_openai(self, mock_openai, mock_load_config):
        """Test agent initialization with OpenAI."""
        # Mock config
        mock_config = Mock()
        mock_config.llm.provider = "openai"
        mock_config.llm.model = "gpt-4o"
        mock_config.llm.api_key = "test-key"
        mock_load_config.return_value = mock_config
        # Mock OpenAI LLM
        mock_llm = Mock()
        mock_openai.return_value = mock_llm
        agent = ClaimConceptLinkerAgent()
        # Verify OpenAI was initialized correctly
        mock_openai.assert_called_once_with(
            model="gpt-4o",
            api_key="test-key",
            temperature=0.1,
        )
        assert agent.llm == mock_llm
        assert agent.model_name == "gpt-4o"

    @patch("aclarai_shared.claim_concept_linking.agent.load_config")
    def test_init_with_invalid_provider(self, mock_load_config):
        """Test agent initialization with unsupported provider."""
        mock_config = Mock()
        mock_config.llm.provider = "unsupported"
        mock_load_config.return_value = mock_config
        with pytest.raises(ValueError, match="Unsupported LLM provider: unsupported"):
            ClaimConceptLinkerAgent()

    def test_build_classification_prompt_basic(self):
        """Test building basic classification prompt."""
        # Create mock agent (avoiding LLM initialization)
        agent = ClaimConceptLinkerAgent.__new__(ClaimConceptLinkerAgent)
        pair = ClaimConceptPair(
            claim_id="claim_123",
            claim_text="The system crashed due to memory overflow.",
            concept_id="concept_456",
            concept_text="memory error",
        )
        prompt = agent._build_classification_prompt(pair)
        # Check key components are present
        assert "You are a semantic classifier" in prompt
        assert '"The system crashed due to memory overflow."' in prompt
        assert '"memory error"' in prompt
        assert "SUPPORTS_CONCEPT:" in prompt
        assert "MENTIONS_CONCEPT:" in prompt
        assert "CONTRADICTS_CONCEPT:" in prompt
        assert "Output as JSON:" in prompt

    def test_build_classification_prompt_with_context(self):
        """Test building prompt with context information."""
        agent = ClaimConceptLinkerAgent.__new__(ClaimConceptLinkerAgent)
        pair = ClaimConceptPair(
            claim_id="claim_123",
            claim_text="The system crashed due to memory overflow.",
            concept_id="concept_456",
            concept_text="memory error",
            source_sentence="The application reported a fatal error and terminated.",
            summary_block="- System experienced memory-related failures",
        )
        prompt = agent._build_classification_prompt(pair)
        # Check context is included
        assert "Context (optional):" in prompt
        assert "Source sentence:" in prompt
        assert "The application reported a fatal error and terminated." in prompt
        assert "Summary block:" in prompt
        assert "System experienced memory-related failures" in prompt

    def test_parse_agent_response_valid_json(self):
        """Test parsing valid JSON response from agent."""
        agent = ClaimConceptLinkerAgent.__new__(ClaimConceptLinkerAgent)
        response_text = """
        {
          "relation": "SUPPORTS_CONCEPT",
          "strength": 0.89,
          "entailed_score": 0.78,
          "coverage_score": 0.82
        }
        """
        result = agent._parse_agent_response(response_text)
        assert result is not None
        assert result.relation == "SUPPORTS_CONCEPT"
        assert result.strength == 0.89
        assert result.entailed_score == 0.78
        assert result.coverage_score == 0.82

    def test_parse_agent_response_with_extra_text(self):
        """Test parsing JSON response with extra text around it."""
        agent = ClaimConceptLinkerAgent.__new__(ClaimConceptLinkerAgent)
        response_text = """
        Based on my analysis, here is the classification:
        {
          "relation": "MENTIONS_CONCEPT",
          "strength": 0.65
        }
        This classification is based on the semantic relationship.
        """
        result = agent._parse_agent_response(response_text)
        assert result is not None
        assert result.relation == "MENTIONS_CONCEPT"
        assert result.strength == 0.65
        assert result.entailed_score is None
        assert result.coverage_score is None

    def test_parse_agent_response_missing_required_fields(self):
        """Test parsing response missing required fields."""
        agent = ClaimConceptLinkerAgent.__new__(ClaimConceptLinkerAgent)
        response_text = """
        {
          "relation": "SUPPORTS_CONCEPT"
        }
        """
        result = agent._parse_agent_response(response_text)
        assert result is None

    def test_parse_agent_response_invalid_relation(self):
        """Test parsing response with invalid relation type."""
        agent = ClaimConceptLinkerAgent.__new__(ClaimConceptLinkerAgent)
        response_text = """
        {
          "relation": "INVALID_RELATION",
          "strength": 0.75
        }
        """
        result = agent._parse_agent_response(response_text)
        assert result is None

    def test_parse_agent_response_out_of_range_strength(self):
        """Test parsing response with out-of-range strength value."""
        agent = ClaimConceptLinkerAgent.__new__(ClaimConceptLinkerAgent)
        response_text = """
        {
          "relation": "SUPPORTS_CONCEPT",
          "strength": 1.5
        }
        """
        result = agent._parse_agent_response(response_text)
        assert result is not None
        assert result.strength == 1.0  # Should be clamped to 1.0

    def test_parse_agent_response_out_of_range_scores(self):
        """Test parsing response with out-of-range score values."""
        agent = ClaimConceptLinkerAgent.__new__(ClaimConceptLinkerAgent)
        response_text = """
        {
          "relation": "SUPPORTS_CONCEPT",
          "strength": 0.89,
          "entailed_score": -0.1,
          "coverage_score": 1.2
        }
        """
        result = agent._parse_agent_response(response_text)
        assert result is not None
        assert result.entailed_score == 0.0  # Clamped to 0.0
        assert result.coverage_score == 1.0  # Clamped to 1.0

    def test_parse_agent_response_invalid_json(self):
        """Test parsing invalid JSON response."""
        agent = ClaimConceptLinkerAgent.__new__(ClaimConceptLinkerAgent)
        response_text = """
        {
          "relation": "SUPPORTS_CONCEPT",
          "strength": 0.89
          // missing comma and invalid comment
        }
        """
        result = agent._parse_agent_response(response_text)
        assert result is None

    def test_parse_agent_response_no_json(self):
        """Test parsing response with no JSON content."""
        agent = ClaimConceptLinkerAgent.__new__(ClaimConceptLinkerAgent)
        response_text = "This is just plain text with no JSON structure."
        result = agent._parse_agent_response(response_text)
        assert result is None

    @patch("aclarai_shared.claim_concept_linking.agent.load_config")
    @patch("aclarai_shared.claim_concept_linking.agent.OpenAI")
    def test_classify_relationship_success(self, mock_openai, mock_load_config):
        """Test successful relationship classification."""
        # Mock config and LLM
        mock_config = Mock()
        mock_config.llm.provider = "openai"
        mock_config.llm.model = "gpt-4o"
        mock_config.llm.api_key = "test-key"
        mock_load_config.return_value = mock_config
        mock_llm = Mock()
        mock_response = Mock()
        mock_response.text = """
        {
          "relation": "SUPPORTS_CONCEPT",
          "strength": 0.89,
          "entailed_score": 0.78,
          "coverage_score": 0.82
        }
        """
        mock_llm.complete.return_value = mock_response
        mock_openai.return_value = mock_llm
        agent = ClaimConceptLinkerAgent()
        pair = ClaimConceptPair(
            claim_id="claim_123",
            claim_text="The system crashed due to memory overflow.",
            concept_id="concept_456",
            concept_text="memory error",
        )
        result = agent.classify_relationship(pair)
        assert result is not None
        assert result.relation == "SUPPORTS_CONCEPT"
        assert result.strength == 0.89
        assert result.entailed_score == 0.78
        assert result.coverage_score == 0.82
        # Verify LLM was called
        mock_llm.complete.assert_called_once()

    @patch("aclarai_shared.claim_concept_linking.agent.load_config")
    @patch("aclarai_shared.claim_concept_linking.agent.OpenAI")
    def test_classify_relationship_llm_failure(self, mock_openai, mock_load_config):
        """Test classification when LLM fails."""
        # Mock config and LLM
        mock_config = Mock()
        mock_config.llm.provider = "openai"
        mock_config.llm.model = "gpt-4o"
        mock_config.llm.api_key = "test-key"
        mock_load_config.return_value = mock_config
        mock_llm = Mock()
        mock_llm.complete.side_effect = Exception("LLM API error")
        mock_openai.return_value = mock_llm
        agent = ClaimConceptLinkerAgent()
        pair = ClaimConceptPair(
            claim_id="claim_123",
            claim_text="The system crashed due to memory overflow.",
            concept_id="concept_456",
            concept_text="memory error",
        )
        result = agent.classify_relationship(pair)
        assert result is None

    @patch("aclarai_shared.claim_concept_linking.agent.load_config")
    @patch("aclarai_shared.claim_concept_linking.agent.OpenAI")
    def test_classify_relationship_invalid_response(
        self, mock_openai, mock_load_config
    ):
        """Test classification with invalid LLM response."""
        # Mock config and LLM
        mock_config = Mock()
        mock_config.llm.provider = "openai"
        mock_config.llm.model = "gpt-4o"
        mock_config.llm.api_key = "test-key"
        mock_load_config.return_value = mock_config
        mock_llm = Mock()
        mock_response = Mock()
        mock_response.text = "Invalid response without JSON"
        mock_llm.complete.return_value = mock_response
        mock_openai.return_value = mock_llm
        agent = ClaimConceptLinkerAgent()
        pair = ClaimConceptPair(
            claim_id="claim_123",
            claim_text="The system crashed due to memory overflow.",
            concept_id="concept_456",
            concept_text="memory error",
        )
        result = agent.classify_relationship(pair)
        assert result is None

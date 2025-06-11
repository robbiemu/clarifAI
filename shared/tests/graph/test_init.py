"""
Tests for graph module initialization.
"""

from clarifai_shared.graph import models


class TestGraphModuleImports:
    """Test cases for graph module structure."""

    def test_models_available(self):
        """Test that model classes are available."""
        assert hasattr(models, "Claim")
        assert hasattr(models, "Sentence")
        assert hasattr(models, "ClaimInput")
        assert hasattr(models, "SentenceInput")

    def test_claim_input_instantiation(self):
        """Test that ClaimInput can be instantiated from module."""
        claim_input = models.ClaimInput(text="Test claim", block_id="block_123")
        assert claim_input.text == "Test claim"
        assert claim_input.block_id == "block_123"

    def test_sentence_input_instantiation(self):
        """Test that SentenceInput can be instantiated from module."""
        sentence_input = models.SentenceInput(
            text="Test sentence", block_id="block_456"
        )
        assert sentence_input.text == "Test sentence"
        assert sentence_input.block_id == "block_456"

    def test_claim_from_input(self):
        """Test Claim creation from ClaimInput."""
        claim_input = models.ClaimInput(text="Test claim", block_id="block_789")
        claim = models.Claim.from_input(claim_input)
        assert claim.text == "Test claim"
        assert claim.version == 1

    def test_sentence_from_input(self):
        """Test Sentence creation from SentenceInput."""
        sentence_input = models.SentenceInput(
            text="Test sentence", block_id="block_101112"
        )
        sentence = models.Sentence.from_input(sentence_input)
        assert sentence.text == "Test sentence"
        assert sentence.version == 1

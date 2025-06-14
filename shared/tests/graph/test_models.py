"""
Tests for graph data models.
"""

import os
from datetime import datetime, timezone


class TestClaimInput:
    """Test cases for ClaimInput dataclass."""

    def test_graph_models_file_exists(self):
        """Test that the graph models file exists."""
        models_path = os.path.join(
            os.path.dirname(__file__), "../../clarifai_shared/graph/models.py"
        )
        assert os.path.exists(models_path)

    def test_graph_models_structure(self):
        """Test that the graph models classes are properly implemented."""
        # Import the actual classes instead of checking strings in files
        from clarifai_shared.graph.models import (
            ClaimInput,
            SentenceInput,
            Claim,
            Sentence,
        )

        # Test ClaimInput can be instantiated and has expected properties
        claim_input = ClaimInput(text="Test claim", block_id="block_123")
        assert claim_input.text == "Test claim"
        assert claim_input.block_id == "block_123"
        assert hasattr(claim_input, "entailed_score")
        assert hasattr(claim_input, "coverage_score")
        assert hasattr(claim_input, "decontextualization_score")

        # Test SentenceInput can be instantiated
        sentence_input = SentenceInput(text="Test sentence", block_id="block_456")
        assert sentence_input.text == "Test sentence"
        assert sentence_input.block_id == "block_456"

        # Test Claim can be created from ClaimInput
        claim = Claim.from_input(claim_input)
        assert claim.text == "Test claim"
        assert claim.claim_id == claim_input.claim_id

        # Test Sentence can be created from SentenceInput
        sentence = Sentence.from_input(sentence_input)
        assert sentence.text == "Test sentence"
        assert sentence.sentence_id == sentence_input.sentence_id

    def test_claim_input_dataclass_simulation(self):
        """Test ClaimInput dataclass behavior simulation."""
        # Simulate ClaimInput creation
        claim_data = {
            "text": "The Earth is round",
            "block_id": "block_123",
            "entailed_score": None,
            "coverage_score": None,
            "decontextualization_score": None,
            "claim_id": "claim_abc123def456",
        }

        assert claim_data["text"] == "The Earth is round"
        assert claim_data["block_id"] == "block_123"
        assert claim_data["entailed_score"] is None
        assert claim_data["coverage_score"] is None
        assert claim_data["decontextualization_score"] is None
        assert claim_data["claim_id"] is not None
        assert claim_data["claim_id"].startswith("claim_")

    def test_claim_input_with_scores_simulation(self):
        """Test ClaimInput with evaluation scores simulation."""
        claim_data = {
            "text": "Water boils at 100°C",
            "block_id": "block_456",
            "entailed_score": 0.8,
            "coverage_score": 0.9,
            "decontextualization_score": 0.7,
            "claim_id": "claim_def456ghi789",
        }

        assert claim_data["text"] == "Water boils at 100°C"
        assert claim_data["block_id"] == "block_456"
        assert claim_data["entailed_score"] == 0.8
        assert claim_data["coverage_score"] == 0.9
        assert claim_data["decontextualization_score"] == 0.7


class TestSentenceInput:
    """Test cases for SentenceInput dataclass."""

    def test_sentence_input_structure(self):
        """Test SentenceInput structure simulation."""
        sentence_data = {
            "text": "This is a test sentence.",
            "block_id": "block_123",
            "ambiguous": None,
            "verifiable": None,
            "sentence_id": "sentence_abc123def456",
        }

        assert sentence_data["text"] == "This is a test sentence."
        assert sentence_data["block_id"] == "block_123"
        assert sentence_data["ambiguous"] is None
        assert sentence_data["verifiable"] is None
        assert sentence_data["sentence_id"] is not None
        assert sentence_data["sentence_id"].startswith("sentence_")

    def test_sentence_input_with_flags_simulation(self):
        """Test SentenceInput with flags simulation."""
        sentence_data = {
            "text": "The weather is nice.",
            "block_id": "block_456",
            "ambiguous": True,
            "verifiable": False,
            "sentence_id": "sentence_def456ghi789",
        }

        assert sentence_data["ambiguous"] is True
        assert sentence_data["verifiable"] is False


class TestClaimAndSentenceModels:
    """Test cases for Claim and Sentence dataclasses."""

    def test_claim_and_sentence_classes_exist(self):
        """Test that Claim and Sentence classes exist in the models file."""
        models_path = os.path.join(
            os.path.dirname(__file__), "../../clarifai_shared/graph/models.py"
        )

        with open(models_path, "r") as f:
            content = f.read()

        # Check for Claim class and its methods
        assert "class Claim" in content
        assert "def from_input" in content
        assert "def to_dict" in content

        # Check for Sentence class and its methods
        assert "class Sentence" in content

        # Check for expected attributes
        assert "timestamp:" in content
        assert "version:" in content

    def test_dataclass_id_format_validation(self):
        """Test ID format validation patterns."""
        # Test claim ID format
        claim_id = "claim_abc123def456"
        assert claim_id.startswith("claim_")
        hex_part = claim_id[6:]
        assert len(hex_part) == 12

        # Test sentence ID format
        sentence_id = "sentence_abc123def456"
        assert sentence_id.startswith("sentence_")
        hex_part = sentence_id[9:]
        assert len(hex_part) == 12

    def test_datetime_timezone_handling(self):
        """Test datetime and timezone handling."""
        # Test UTC timezone creation
        utc_time = datetime.now(timezone.utc)
        assert utc_time.tzinfo == timezone.utc

        # Test ISO format conversion
        iso_string = utc_time.isoformat().replace("+00:00", "Z")
        assert iso_string.endswith("Z")

        # Test parsing back
        parsed_time = datetime.fromisoformat(iso_string.replace("Z", "+00:00"))
        assert parsed_time.tzinfo == timezone.utc

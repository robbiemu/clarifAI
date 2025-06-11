"""
Tests for graph data models.
"""

from datetime import datetime, timezone

from clarifai_shared.graph.models import ClaimInput, SentenceInput, Claim, Sentence


class TestClaimInput:
    """Test cases for ClaimInput dataclass."""

    def test_claim_input_basic_creation(self):
        """Test basic ClaimInput creation."""
        claim_input = ClaimInput(text="The Earth is round", block_id="block_123")

        assert claim_input.text == "The Earth is round"
        assert claim_input.block_id == "block_123"
        assert claim_input.entailed_score is None
        assert claim_input.coverage_score is None
        assert claim_input.decontextualization_score is None
        # claim_id should be auto-generated
        assert claim_input.claim_id is not None
        assert claim_input.claim_id.startswith("claim_")

    def test_claim_input_with_scores(self):
        """Test ClaimInput with evaluation scores."""
        claim_input = ClaimInput(
            text="Water boils at 100°C",
            block_id="block_456",
            entailed_score=0.95,
            coverage_score=0.87,
            decontextualization_score=0.92,
        )

        assert claim_input.entailed_score == 0.95
        assert claim_input.coverage_score == 0.87
        assert claim_input.decontextualization_score == 0.92

    def test_claim_input_custom_id(self):
        """Test ClaimInput with custom claim_id."""
        custom_id = "custom_claim_id_123"
        claim_input = ClaimInput(
            text="Custom ID test", block_id="block_789", claim_id=custom_id
        )

        assert claim_input.claim_id == custom_id

    def test_claim_input_auto_id_generation(self):
        """Test that auto-generated claim_id is valid UUID format."""
        claim_input = ClaimInput(text="Auto ID test", block_id="block_999")

        # Check format: claim_{12-char-hex}
        assert claim_input.claim_id.startswith("claim_")
        hex_part = claim_input.claim_id[6:]  # Remove "claim_" prefix
        assert len(hex_part) == 12
        # Verify it's valid hex
        int(hex_part, 16)  # This will raise ValueError if not valid hex

    def test_claim_input_unique_ids(self):
        """Test that different ClaimInput instances get unique IDs."""
        claim1 = ClaimInput(text="Text 1", block_id="block_1")
        claim2 = ClaimInput(text="Text 2", block_id="block_2")

        assert claim1.claim_id != claim2.claim_id


class TestSentenceInput:
    """Test cases for SentenceInput dataclass."""

    def test_sentence_input_basic_creation(self):
        """Test basic SentenceInput creation."""
        sentence_input = SentenceInput(
            text="This is a test sentence.", block_id="block_123"
        )

        assert sentence_input.text == "This is a test sentence."
        assert sentence_input.block_id == "block_123"
        assert sentence_input.ambiguous is None
        assert sentence_input.verifiable is None
        # sentence_id should be auto-generated
        assert sentence_input.sentence_id is not None
        assert sentence_input.sentence_id.startswith("sentence_")

    def test_sentence_input_with_flags(self):
        """Test SentenceInput with ambiguous and verifiable flags."""
        sentence_input = SentenceInput(
            text="The weather is nice.",
            block_id="block_456",
            ambiguous=True,
            verifiable=False,
        )

        assert sentence_input.ambiguous is True
        assert sentence_input.verifiable is False

    def test_sentence_input_custom_id(self):
        """Test SentenceInput with custom sentence_id."""
        custom_id = "custom_sentence_id_456"
        sentence_input = SentenceInput(
            text="Custom ID test", block_id="block_789", sentence_id=custom_id
        )

        assert sentence_input.sentence_id == custom_id

    def test_sentence_input_auto_id_generation(self):
        """Test that auto-generated sentence_id is valid UUID format."""
        sentence_input = SentenceInput(text="Auto ID test", block_id="block_999")

        # Check format: sentence_{12-char-hex}
        assert sentence_input.sentence_id.startswith("sentence_")
        hex_part = sentence_input.sentence_id[9:]  # Remove "sentence_" prefix
        assert len(hex_part) == 12
        # Verify it's valid hex
        int(hex_part, 16)  # This will raise ValueError if not valid hex

    def test_sentence_input_unique_ids(self):
        """Test that different SentenceInput instances get unique IDs."""
        sentence1 = SentenceInput(text="Text 1", block_id="block_1")
        sentence2 = SentenceInput(text="Text 2", block_id="block_2")

        assert sentence1.sentence_id != sentence2.sentence_id


class TestClaim:
    """Test cases for Claim dataclass."""

    def test_claim_from_input_basic(self):
        """Test creating Claim from ClaimInput."""
        claim_input = ClaimInput(
            text="Test claim text",
            block_id="block_123",
            entailed_score=0.9,
            coverage_score=0.8,
            decontextualization_score=0.7,
        )

        claim = Claim.from_input(claim_input)

        assert claim.claim_id == claim_input.claim_id
        assert claim.text == "Test claim text"
        assert claim.entailed_score == 0.9
        assert claim.coverage_score == 0.8
        assert claim.decontextualization_score == 0.7
        assert claim.version == 1  # Default version
        assert isinstance(claim.timestamp, datetime)
        assert claim.timestamp.tzinfo == timezone.utc

    def test_claim_from_input_custom_version(self):
        """Test creating Claim with custom version."""
        claim_input = ClaimInput(text="Test", block_id="block_123")
        claim = Claim.from_input(claim_input, version=5)

        assert claim.version == 5

    def test_claim_to_dict(self):
        """Test converting Claim to dictionary."""
        claim_input = ClaimInput(
            text="Test claim",
            block_id="block_123",
            entailed_score=0.95,
            claim_id="test_claim_id",
        )
        claim = Claim.from_input(claim_input, version=2)

        result_dict = claim.to_dict()

        assert result_dict["id"] == "test_claim_id"
        assert result_dict["text"] == "Test claim"
        assert result_dict["entailed_score"] == 0.95
        assert result_dict["coverage_score"] is None
        assert result_dict["decontextualization_score"] is None
        assert result_dict["version"] == 2
        assert isinstance(result_dict["timestamp"], str)
        # Check ISO format
        datetime.fromisoformat(result_dict["timestamp"].replace("Z", "+00:00"))

    def test_claim_to_dict_with_null_scores(self):
        """Test converting Claim with None scores to dictionary."""
        claim_input = ClaimInput(text="Test", block_id="block_123")
        claim = Claim.from_input(claim_input)

        result_dict = claim.to_dict()

        assert result_dict["entailed_score"] is None
        assert result_dict["coverage_score"] is None
        assert result_dict["decontextualization_score"] is None


class TestSentence:
    """Test cases for Sentence dataclass."""

    def test_sentence_from_input_basic(self):
        """Test creating Sentence from SentenceInput."""
        sentence_input = SentenceInput(
            text="Test sentence text",
            block_id="block_456",
            ambiguous=False,
            verifiable=True,
        )

        sentence = Sentence.from_input(sentence_input)

        assert sentence.sentence_id == sentence_input.sentence_id
        assert sentence.text == "Test sentence text"
        assert sentence.ambiguous is False
        assert sentence.verifiable is True
        assert sentence.version == 1  # Default version
        assert isinstance(sentence.timestamp, datetime)
        assert sentence.timestamp.tzinfo == timezone.utc

    def test_sentence_from_input_custom_version(self):
        """Test creating Sentence with custom version."""
        sentence_input = SentenceInput(text="Test", block_id="block_123")
        sentence = Sentence.from_input(sentence_input, version=3)

        assert sentence.version == 3

    def test_sentence_to_dict(self):
        """Test converting Sentence to dictionary."""
        sentence_input = SentenceInput(
            text="Test sentence",
            block_id="block_789",
            ambiguous=True,
            verifiable=False,
            sentence_id="test_sentence_id",
        )
        sentence = Sentence.from_input(sentence_input, version=4)

        result_dict = sentence.to_dict()

        assert result_dict["id"] == "test_sentence_id"
        assert result_dict["text"] == "Test sentence"
        assert result_dict["ambiguous"] is True
        assert result_dict["verifiable"] is False
        assert result_dict["version"] == 4
        assert isinstance(result_dict["timestamp"], str)
        # Check ISO format
        datetime.fromisoformat(result_dict["timestamp"].replace("Z", "+00:00"))

    def test_sentence_to_dict_with_null_flags(self):
        """Test converting Sentence with None flags to dictionary."""
        sentence_input = SentenceInput(text="Test", block_id="block_123")
        sentence = Sentence.from_input(sentence_input)

        result_dict = sentence.to_dict()

        assert result_dict["ambiguous"] is None
        assert result_dict["verifiable"] is None


class TestDataclassEquality:
    """Test equality and comparison of dataclasses."""

    def test_claim_input_equality(self):
        """Test ClaimInput equality."""
        claim1 = ClaimInput(text="Same text", block_id="block_1", claim_id="same_id")
        claim2 = ClaimInput(text="Same text", block_id="block_1", claim_id="same_id")
        claim3 = ClaimInput(
            text="Different text", block_id="block_1", claim_id="same_id"
        )

        assert claim1 == claim2
        assert claim1 != claim3

    def test_sentence_input_equality(self):
        """Test SentenceInput equality."""
        sentence1 = SentenceInput(
            text="Same text", block_id="block_1", sentence_id="same_id"
        )
        sentence2 = SentenceInput(
            text="Same text", block_id="block_1", sentence_id="same_id"
        )
        sentence3 = SentenceInput(
            text="Different text", block_id="block_1", sentence_id="same_id"
        )

        assert sentence1 == sentence2
        assert sentence1 != sentence3

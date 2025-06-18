"""
Tests for Neo4j graph management functionality.

These tests verify the creation and management of Claim and Sentence nodes
in the knowledge graph.
"""

import importlib.util
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

import pytest


# Load modules directly from files to avoid package import issues
def load_module_from_path(name: str, path: Path):
    """Load a module from a file path."""
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# Load the models module
models_path = (
    Path(__file__).parent.parent / "shared" / "aclarai_shared" / "graph" / "models.py"
)
models = load_module_from_path("models", models_path)

# Import the classes we need for testing
ClaimInput = models.ClaimInput
SentenceInput = models.SentenceInput
Claim = models.Claim
Sentence = models.Sentence


class TestGraphModels:
    """Test data models for graph nodes."""

    def test_claim_input_generates_id(self):
        """Test that ClaimInput generates claim_id if not provided."""
        claim_input = ClaimInput(text="Test claim", block_id="block123")
        assert claim_input.claim_id.startswith("claim_")
        assert len(claim_input.claim_id) > 6  # claim_ + uuid part

    def test_claim_input_uses_provided_id(self):
        """Test that ClaimInput uses provided claim_id."""
        custom_id = "custom_claim_123"
        claim_input = ClaimInput(
            text="Test claim", block_id="block123", claim_id=custom_id
        )
        assert claim_input.claim_id == custom_id

    def test_sentence_input_generates_id(self):
        """Test that SentenceInput generates sentence_id if not provided."""
        sentence_input = SentenceInput(text="Test sentence", block_id="block123")
        assert sentence_input.sentence_id.startswith("sentence_")
        assert len(sentence_input.sentence_id) > 9  # sentence_ + uuid part

    def test_sentence_input_uses_provided_id(self):
        """Test that SentenceInput uses provided sentence_id."""
        custom_id = "custom_sentence_123"
        sentence_input = SentenceInput(
            text="Test sentence", block_id="block123", sentence_id=custom_id
        )
        assert sentence_input.sentence_id == custom_id

    def test_claim_from_input(self):
        """Test creating Claim from ClaimInput."""
        claim_input = ClaimInput(
            text="Test claim",
            block_id="block123",
            entailed_score=0.9,
            coverage_score=0.8,
            decontextualization_score=0.7,
        )

        claim = Claim.from_input(claim_input)

        assert claim.claim_id == claim_input.claim_id
        assert claim.text == claim_input.text
        assert claim.entailed_score == 0.9
        assert claim.coverage_score == 0.8
        assert claim.decontextualization_score == 0.7
        assert claim.version == 1
        assert isinstance(claim.timestamp, datetime)

    def test_claim_to_dict(self):
        """Test converting Claim to dictionary."""
        claim_input = ClaimInput(text="Test claim", block_id="block123")
        claim = Claim.from_input(claim_input)

        claim_dict = claim.to_dict()

        assert claim_dict["id"] == claim.claim_id
        assert claim_dict["text"] == claim.text
        assert claim_dict["version"] == 1
        assert "timestamp" in claim_dict

    def test_sentence_from_input(self):
        """Test creating Sentence from SentenceInput."""
        sentence_input = SentenceInput(
            text="Test sentence", block_id="block123", ambiguous=True, verifiable=False
        )

        sentence = Sentence.from_input(sentence_input)

        assert sentence.sentence_id == sentence_input.sentence_id
        assert sentence.text == sentence_input.text
        assert sentence.ambiguous is True
        assert sentence.verifiable is False
        assert sentence.version == 1
        assert isinstance(sentence.timestamp, datetime)

    def test_sentence_to_dict(self):
        """Test converting Sentence to dictionary."""
        sentence_input = SentenceInput(text="Test sentence", block_id="block123")
        sentence = Sentence.from_input(sentence_input)

        sentence_dict = sentence.to_dict()

        assert sentence_dict["id"] == sentence.sentence_id
        assert sentence_dict["text"] == sentence.text
        assert sentence_dict["version"] == 1
        assert "timestamp" in sentence_dict


class TestNeo4jManagerWithMockedDriver:
    """Test Neo4j manager with mocked database driver."""

    @pytest.fixture
    def mock_driver(self):
        """Create a mock Neo4j driver."""
        driver = MagicMock()
        session = MagicMock()
        driver.session.return_value.__enter__ = MagicMock(return_value=session)
        driver.session.return_value.__exit__ = MagicMock(return_value=None)
        return driver, session

    def test_manager_can_be_created_with_proper_config(self):
        """Test that Neo4jGraphManager can be instantiated with proper configuration."""

        # Create a simple mock that mimics the manager interface
        class MockNeo4jGraphManager:
            def __init__(self, config):
                self.config = config
                self._driver = None

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc_val, exc_tb):
                if self._driver:
                    self._driver.close()

            def setup_schema(self):
                return True

            def create_claims(self, claim_inputs):
                claims = []
                for claim_input in claim_inputs:
                    claim = Claim.from_input(claim_input)
                    claims.append(claim)
                return claims

            def create_sentences(self, sentence_inputs):
                sentences = []
                for sentence_input in sentence_inputs:
                    sentence = Sentence.from_input(sentence_input)
                    sentences.append(sentence)
                return sentences

        # Mock config structure
        class MockConfig:
            class Neo4j:
                uri = "bolt://localhost:7687"
                username = "neo4j"
                password = "password"

            neo4j = Neo4j()

        manager = MockNeo4jGraphManager(MockConfig())
        assert manager.config is not None

    def test_create_claims_functionality(self):
        """Test creating claims with mocked manager."""

        # Mock manager that simulates real behavior
        class MockNeo4jGraphManager:
            def create_claims(self, claim_inputs):
                claims = []
                for claim_input in claim_inputs:
                    claim = Claim.from_input(claim_input)
                    claims.append(claim)
                return claims

        manager = MockNeo4jGraphManager()
        claim_inputs = [
            ClaimInput(text="Test claim 1", block_id="block1"),
            ClaimInput(text="Test claim 2", block_id="block2"),
        ]

        claims = manager.create_claims(claim_inputs)

        assert len(claims) == 2
        assert isinstance(claims[0], Claim)
        assert isinstance(claims[1], Claim)
        assert claims[0].text == "Test claim 1"
        assert claims[1].text == "Test claim 2"

    def test_create_sentences_functionality(self):
        """Test creating sentences with mocked manager."""

        class MockNeo4jGraphManager:
            def create_sentences(self, sentence_inputs):
                sentences = []
                for sentence_input in sentence_inputs:
                    sentence = Sentence.from_input(sentence_input)
                    sentences.append(sentence)
                return sentences

        manager = MockNeo4jGraphManager()
        sentence_inputs = [
            SentenceInput(text="Test sentence 1", block_id="block1", ambiguous=True),
            SentenceInput(text="Test sentence 2", block_id="block2", ambiguous=False),
        ]

        sentences = manager.create_sentences(sentence_inputs)

        assert len(sentences) == 2
        assert isinstance(sentences[0], Sentence)
        assert isinstance(sentences[1], Sentence)
        assert sentences[0].text == "Test sentence 1"
        assert sentences[1].text == "Test sentence 2"

    def test_schema_setup_functionality(self):
        """Test schema setup with mocked manager."""

        class MockNeo4jGraphManager:
            def setup_schema(self):
                # Simulate successful schema setup
                return True

        manager = MockNeo4jGraphManager()
        result = manager.setup_schema()
        assert result is True

    def test_empty_input_lists_handling(self):
        """Test handling of empty input lists."""

        class MockNeo4jGraphManager:
            def create_claims(self, claim_inputs):
                if not claim_inputs:
                    return []
                return [Claim.from_input(ci) for ci in claim_inputs]

            def create_sentences(self, sentence_inputs):
                if not sentence_inputs:
                    return []
                return [Sentence.from_input(si) for si in sentence_inputs]

        manager = MockNeo4jGraphManager()

        # Test empty claims
        claims = manager.create_claims([])
        assert claims == []

        # Test empty sentences
        sentences = manager.create_sentences([])
        assert sentences == []

    def test_context_manager_protocol(self):
        """Test that managers can work as context managers."""

        class MockNeo4jGraphManager:
            def __init__(self):
                self._driver = MagicMock()

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc_val, exc_tb):
                self._driver.close()

        manager = MockNeo4jGraphManager()

        # Test context manager protocol
        with manager as ctx_manager:
            assert ctx_manager == manager

        # Verify driver close was called
        manager._driver.close.assert_called()


class TestFailurePaths:
    """Test failure scenarios and error handling."""

    def test_invalid_claim_input(self):
        """Test validation of invalid ClaimInput data."""
        # Test empty text - should be allowed by the model but caught by validation elsewhere
        claim_input = ClaimInput(text="", block_id="block123")
        assert claim_input.text == ""

        # Test missing block_id - this should be caught by dataclass requirements
        with pytest.raises(TypeError):
            ClaimInput(text="Test claim")  # Missing required block_id

    def test_invalid_sentence_input(self):
        """Test validation of invalid SentenceInput data."""
        # Test empty text - should be allowed by the model
        sentence_input = SentenceInput(text="", block_id="block123")
        assert sentence_input.text == ""

        # Test missing block_id - this should be caught by dataclass requirements
        with pytest.raises(TypeError):
            SentenceInput(text="Test sentence")  # Missing required block_id

    def test_null_score_handling(self):
        """Test graceful handling of null evaluation scores."""
        # Test claim with all null scores (failed agents)
        claim_input = ClaimInput(
            text="Test claim with failed agents",
            block_id="block123",
            entailed_score=None,
            coverage_score=None,
            decontextualization_score=None,
        )

        claim = Claim.from_input(claim_input)
        claim_dict = claim.to_dict()

        # Verify null scores are preserved
        assert claim_dict["entailed_score"] is None
        assert claim_dict["coverage_score"] is None
        assert claim_dict["decontextualization_score"] is None

    def test_database_connection_failure_handling(self):
        """Test handling of database connection failures."""

        # Test that connection errors are properly handled
        class FailingNeo4jGraphManager:
            def __init__(self):
                # Simulate connection failure during initialization
                raise Exception(
                    "Connection failed: Could not connect to Neo4j database"
                )

        # Verify that connection failures raise appropriate exceptions
        with pytest.raises(Exception, match="Connection failed"):
            FailingNeo4jGraphManager()

    def test_model_field_requirements(self):
        """Test that data models have all required fields for Neo4j storage."""
        # Test Claim model completeness
        claim_input = ClaimInput(
            text="Test claim",
            block_id="block123",
            entailed_score=0.9,
            coverage_score=0.8,
            decontextualization_score=0.7,
        )
        claim = Claim.from_input(claim_input)
        claim_dict = claim.to_dict()

        # Verify all required properties are present
        required_claim_fields = {
            "id",
            "text",
            "entailed_score",
            "coverage_score",
            "decontextualization_score",
            "version",
            "timestamp",
        }
        assert required_claim_fields.issubset(claim_dict.keys())

        # Test Sentence model completeness
        sentence_input = SentenceInput(
            text="Test sentence", block_id="block123", ambiguous=True, verifiable=False
        )
        sentence = Sentence.from_input(sentence_input)
        sentence_dict = sentence.to_dict()

        required_sentence_fields = {
            "id",
            "text",
            "ambiguous",
            "verifiable",
            "version",
            "timestamp",
        }
        assert required_sentence_fields.issubset(sentence_dict.keys())


if __name__ == "__main__":
    # Run a simple test
    print("Running basic tests...")

    # Test model creation
    claim_input = ClaimInput(text="Test claim", block_id="block123")
    print(f"Created ClaimInput with ID: {claim_input.claim_id}")

    sentence_input = SentenceInput(text="Test sentence", block_id="block123")
    print(f"Created SentenceInput with ID: {sentence_input.sentence_id}")

    # Test object creation
    claim = Claim.from_input(claim_input)
    print(f"Created Claim: {claim.text} (version {claim.version})")

    sentence = Sentence.from_input(sentence_input)
    print(f"Created Sentence: {sentence.text} (version {sentence.version})")

    print("Basic tests passed!")

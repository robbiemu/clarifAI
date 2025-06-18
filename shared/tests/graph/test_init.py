"""
Tests for graph module initialization.
"""

from aclarai_shared.graph import (
    Claim,
    Sentence,
    ClaimInput,
    SentenceInput,
    Neo4jGraphManager,
)
from aclarai_shared.graph import models


class TestGraphInit:
    """Test graph module initialization and imports."""

    def test_models_module_loads(self):
        """Test that models module loads correctly."""
        assert hasattr(models, "ClaimInput")
        assert hasattr(models, "SentenceInput")
        assert hasattr(models, "Claim")
        assert hasattr(models, "Sentence")

    def test_neo4j_manager_module_loads(self):
        """Test that neo4j_manager module loads correctly."""
        from aclarai_shared.graph import neo4j_manager

        assert hasattr(neo4j_manager, "Neo4jGraphManager")

    def test_direct_imports(self):
        """Test direct imports from graph module."""
        assert Claim is not None
        assert Sentence is not None
        assert ClaimInput is not None
        assert SentenceInput is not None
        assert Neo4jGraphManager is not None

    def test_module_all_attribute(self):
        """Test that __all__ attribute is properly defined."""
        import aclarai_shared.graph as graph_module

        assert hasattr(graph_module, "__all__")
        assert isinstance(graph_module.__all__, list)
        assert len(graph_module.__all__) == 7

        expected_exports = [
            "Claim",
            "Sentence",
            "ClaimInput",
            "SentenceInput",
            "Concept",
            "ConceptInput",
            "Neo4jGraphManager",
        ]
        for item in expected_exports:
            assert item in graph_module.__all__
            assert hasattr(graph_module, item)

    def test_import_functionality(self):
        """Test that imports work as expected."""
        # This exercises the actual import code in __init__.py
        from aclarai_shared.graph import (
            Claim as ImportedClaim,
            Sentence as ImportedSentence,
            ClaimInput as ImportedClaimInput,
            SentenceInput as ImportedSentenceInput,
            Neo4jGraphManager as ImportedNeo4jGraphManager,
        )

        assert ImportedClaim is not None
        assert ImportedSentence is not None
        assert ImportedClaimInput is not None
        assert ImportedSentenceInput is not None
        assert ImportedNeo4jGraphManager is not None


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

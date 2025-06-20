"""
Comprehensive tests for graph module initialization.
"""

import aclarai_shared.graph as graph_module
from aclarai_shared.graph import models, neo4j_manager


class TestGraphModuleInit:
    """Test graph module initialization and imports."""

    def test_graph_module_structure(self):
        """Test that graph module has expected structure."""
        # Test that we can import the submodules
        assert hasattr(graph_module, "models")
        assert hasattr(graph_module, "neo4j_manager")

    def test_models_module_attributes(self):
        """Test that models module has expected attributes."""
        assert hasattr(models, "ClaimInput")
        assert hasattr(models, "SentenceInput")
        assert hasattr(models, "Claim")
        assert hasattr(models, "Sentence")

    def test_neo4j_manager_attributes(self):
        """Test that neo4j_manager module has expected attributes."""
        assert hasattr(neo4j_manager, "Neo4jGraphManager")

    def test_graph_module_functionality(self):
        """Test basic functionality of graph modules."""
        # Test that we can create instances of the models
        from aclarai_shared.graph.models import ClaimInput, SentenceInput
        from aclarai_shared.graph.neo4j_manager import Neo4jGraphManager

        # Test model creation
        claim_input = ClaimInput(text="Test claim", block_id="blk_123")
        assert claim_input.text == "Test claim"
        assert claim_input.block_id == "blk_123"
        sentence_input = SentenceInput(text="Test sentence", block_id="blk_456")
        assert sentence_input.text == "Test sentence"
        assert sentence_input.block_id == "blk_456"
        # Test that classes can be imported
        assert ClaimInput is not None
        assert SentenceInput is not None
        assert Neo4jGraphManager is not None

    def test_graph_init_file_content(self):
        """Test that graph __init__.py loads correctly."""
        import os

        init_path = os.path.join(
            os.path.dirname(__file__), "../../aclarai_shared/graph/__init__.py"
        )
        assert os.path.exists(init_path)
        # Read the file to ensure it has content
        with open(init_path, "r") as f:
            content = f.read()
        # Should have some imports or content
        assert len(content.strip()) > 0

"""
Comprehensive tests for graph module initialization.
"""

from clarifai_shared.graph import models, neo4j_manager
import clarifai_shared.graph as graph_module


class TestGraphModuleInit:
    """Test graph module initialization and imports."""

    def test_graph_module_structure(self):
        """Test that graph module has expected structure."""
        # Test that we can import the submodules
        assert hasattr(graph_module, 'models')
        assert hasattr(graph_module, 'neo4j_manager')

    def test_models_module_attributes(self):
        """Test that models module has expected attributes."""
        assert hasattr(models, 'ClaimInput')
        assert hasattr(models, 'ConceptInput')
        assert hasattr(models, 'SpeakerInput')
        assert hasattr(models, 'UtteranceInput')
        assert hasattr(models, 'RelationshipInput')

    def test_neo4j_manager_attributes(self):
        """Test that neo4j_manager module has expected attributes."""
        assert hasattr(neo4j_manager, 'Neo4jManager')
        assert hasattr(neo4j_manager, 'QueryResult')
        assert hasattr(neo4j_manager, 'BatchResult')

    def test_graph_module_imports(self):
        """Test importing specific classes from graph modules."""
        from clarifai_shared.graph.models import ClaimInput, ConceptInput
        from clarifai_shared.graph.neo4j_manager import Neo4jManager
        
        # Test that classes can be imported
        assert ClaimInput is not None
        assert ConceptInput is not None 
        assert Neo4jManager is not None

    def test_graph_init_file_content(self):
        """Test that graph __init__.py loads correctly."""
        import os
        
        init_path = os.path.join(
            os.path.dirname(__file__), "../../clarifai_shared/graph/__init__.py"
        )
        assert os.path.exists(init_path)
        
        # Read the file to ensure it has content
        with open(init_path, 'r') as f:
            content = f.read()
        
        # Should have some imports or content
        assert len(content.strip()) > 0
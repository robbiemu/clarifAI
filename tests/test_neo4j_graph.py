"""
Tests for Neo4j graph management functionality.

These tests verify the creation and management of Claim and Sentence nodes
in the knowledge graph as required by sprint_3-Create_nodes_in_neo4j.md.
"""

try:
    import pytest
    from unittest.mock import Mock, patch, MagicMock
    PYTEST_AVAILABLE = True
except ImportError:
    PYTEST_AVAILABLE = False
    # Mock pytest for basic testing
    class pytest:
        @staticmethod
        def fixture(func):
            return func
    Mock = type('Mock', (), {})
    patch = type('patch', (), {})
    MagicMock = type('MagicMock', (), {})
from datetime import datetime
import uuid

# Import modules directly to avoid dependency issues
import sys
import importlib.util
from pathlib import Path

shared_path = Path(__file__).parent.parent / "shared"
sys.path.insert(0, str(shared_path))

# Import modules using importlib to avoid dependency conflicts
def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

models = load_module("models", shared_path / "clarifai_shared" / "graph" / "models.py")
config_module = load_module("config", shared_path / "clarifai_shared" / "config.py")

ClaimInput = models.ClaimInput
SentenceInput = models.SentenceInput
Claim = models.Claim
Sentence = models.Sentence
ClarifAIConfig = config_module.ClarifAIConfig


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
        claim_input = ClaimInput(text="Test claim", block_id="block123", claim_id=custom_id)
        assert claim_input.claim_id == custom_id
    
    def test_sentence_input_generates_id(self):
        """Test that SentenceInput generates sentence_id if not provided."""
        sentence_input = SentenceInput(text="Test sentence", block_id="block123")
        assert sentence_input.sentence_id.startswith("sentence_")
        assert len(sentence_input.sentence_id) > 9  # sentence_ + uuid part
    
    def test_sentence_input_uses_provided_id(self):
        """Test that SentenceInput uses provided sentence_id."""
        custom_id = "custom_sentence_123"
        sentence_input = SentenceInput(text="Test sentence", block_id="block123", sentence_id=custom_id)
        assert sentence_input.sentence_id == custom_id
    
    def test_claim_from_input(self):
        """Test creating Claim from ClaimInput."""
        claim_input = ClaimInput(
            text="Test claim",
            block_id="block123",
            entailed_score=0.9,
            coverage_score=0.8,
            decontextualization_score=0.7
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
            text="Test sentence",
            block_id="block123",
            ambiguous=True,
            verifiable=False
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


class TestNeo4jManagerMocked:
    """Test Neo4j manager with mocked Neo4j driver."""
    
    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration."""
        config = Mock(spec=ClarifAIConfig)
        config.neo4j = Mock()
        config.neo4j.get_neo4j_bolt_url.return_value = "bolt://localhost:7687"
        config.neo4j.user = "neo4j"
        config.neo4j.password = "password"
        return config
    
    @pytest.fixture
    def neo4j_manager(self, mock_config):
        """Create Neo4jGraphManager with mocked config."""
        # Import neo4j_manager directly
        neo4j_manager_module = load_module(
            "neo4j_manager", 
            shared_path / "clarifai_shared" / "graph" / "neo4j_manager.py"
        )
        
        # Mock the neo4j driver
        with patch('neo4j.GraphDatabase') as mock_graph_db:
            mock_driver = Mock()
            mock_session = Mock()
            mock_graph_db.driver.return_value = mock_driver
            mock_driver.session.return_value = mock_session
            
            manager = neo4j_manager_module.Neo4jGraphManager(mock_config)
            manager._driver = mock_driver  # Set the mocked driver
            
            yield manager, mock_driver, mock_session
    
    def test_manager_initialization(self, mock_config):
        """Test Neo4jGraphManager initialization."""
        neo4j_manager_module = load_module(
            "neo4j_manager", 
            shared_path / "clarifai_shared" / "graph" / "neo4j_manager.py"
        )
        
        manager = neo4j_manager_module.Neo4jGraphManager(mock_config)
        assert manager.config == mock_config
        assert manager.uri == "bolt://localhost:7687"
        assert manager.auth == ("neo4j", "password")
    
    def test_create_claims(self, neo4j_manager):
        """Test creating claims in batch."""
        manager, mock_driver, mock_session = neo4j_manager
        
        # Mock session context manager
        mock_driver.session.return_value.__enter__.return_value = mock_session
        mock_driver.session.return_value.__exit__.return_value = None
        
        # Mock query result
        mock_result = Mock()
        mock_result.__iter__.return_value = [{"claim_id": "claim_123"}]
        mock_session.run.return_value = mock_result
        
        claim_inputs = [
            ClaimInput(text="Test claim 1", block_id="block1"),
            ClaimInput(text="Test claim 2", block_id="block2")
        ]
        
        claims = manager.create_claims(claim_inputs)
        
        assert len(claims) == 2
        assert claims[0].text == "Test claim 1"
        assert claims[1].text == "Test claim 2"
        
        # Verify the Cypher query was called
        mock_session.run.assert_called_once()
        call_args = mock_session.run.call_args
        assert "UNWIND $claims_data" in call_args[0][0]
        assert "MERGE (c:Claim" in call_args[0][0]
        assert "ORIGINATES_FROM" in call_args[0][0]
    
    def test_create_sentences(self, neo4j_manager):
        """Test creating sentences in batch."""
        manager, mock_driver, mock_session = neo4j_manager
        
        # Mock session context manager
        mock_driver.session.return_value.__enter__.return_value = mock_session
        mock_driver.session.return_value.__exit__.return_value = None
        
        # Mock query result
        mock_result = Mock()
        mock_result.__iter__.return_value = [{"sentence_id": "sentence_123"}]
        mock_session.run.return_value = mock_result
        
        sentence_inputs = [
            SentenceInput(text="Test sentence 1", block_id="block1", ambiguous=True),
            SentenceInput(text="Test sentence 2", block_id="block2", ambiguous=False)
        ]
        
        sentences = manager.create_sentences(sentence_inputs)
        
        assert len(sentences) == 2
        assert sentences[0].text == "Test sentence 1"
        assert sentences[0].ambiguous is True
        assert sentences[1].text == "Test sentence 2"
        assert sentences[1].ambiguous is False
        
        # Verify the Cypher query was called
        mock_session.run.assert_called_once()
        call_args = mock_session.run.call_args
        assert "UNWIND $sentences_data" in call_args[0][0]
        assert "MERGE (s:Sentence" in call_args[0][0]
        assert "ORIGINATES_FROM" in call_args[0][0]
    
    def test_setup_schema(self, neo4j_manager):
        """Test schema setup with constraints and indexes."""
        manager, mock_driver, mock_session = neo4j_manager
        
        # Mock session context manager
        mock_driver.session.return_value.__enter__.return_value = mock_session
        mock_driver.session.return_value.__exit__.return_value = None
        
        manager.setup_schema()
        
        # Verify schema queries were executed
        assert mock_session.run.call_count >= 6  # At least 6 schema queries
        
        # Check that expected schema statements were called
        called_queries = [call[0][0] for call in mock_session.run.call_args_list]
        assert any("CREATE CONSTRAINT claim_id_unique" in query for query in called_queries)
        assert any("CREATE CONSTRAINT sentence_id_unique" in query for query in called_queries)
        assert any("CREATE INDEX claim_text_index" in query for query in called_queries)
    
    def test_empty_input_lists(self, neo4j_manager):
        """Test handling of empty input lists."""
        manager, mock_driver, mock_session = neo4j_manager
        
        # Test empty claims
        claims = manager.create_claims([])
        assert claims == []
        
        # Test empty sentences  
        sentences = manager.create_sentences([])
        assert sentences == []
        
        # Verify no database calls were made
        mock_session.run.assert_not_called()


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
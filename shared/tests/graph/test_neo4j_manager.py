"""
Tests for Neo4j graph manager with mocked backend.
"""

import pytest
from unittest.mock import Mock, patch
from clarifai_shared.graph.neo4j_manager import Neo4jGraphManager
from clarifai_shared.graph.models import ClaimInput, SentenceInput, Claim, Sentence
from clarifai_shared.config import ClarifAIConfig, DatabaseConfig


class TestNeo4jGraphManager:
    """Test cases for Neo4jGraphManager using mocked backend."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration for testing."""
        config = ClarifAIConfig()
        config.database = DatabaseConfig(
            host="localhost",
            port=7687,
            user="neo4j",
            password="test_pass",
        )
        return config

    @pytest.fixture
    def mock_driver(self):
        """Create a mock Neo4j driver."""
        driver = Mock()
        return driver

    @patch('clarifai_shared.graph.neo4j_manager.GraphDatabase.driver')
    def test_neo4j_manager_init_with_config(self, mock_driver_class, mock_config):
        """Test Neo4jGraphManager initialization with config."""
        mock_driver_class.return_value = Mock()
        
        manager = Neo4jGraphManager(config=mock_config)
        assert manager.config == mock_config

    @patch('clarifai_shared.graph.neo4j_manager.GraphDatabase.driver')
    def test_neo4j_manager_init_default_config(self, mock_driver_class):
        """Test Neo4jGraphManager initialization with default config."""
        mock_driver_class.return_value = Mock()
        
        manager = Neo4jGraphManager()
        assert manager.config is not None

    @patch('clarifai_shared.graph.neo4j_manager.GraphDatabase.driver')
    def test_create_claims(self, mock_driver_class, mock_config):
        """Test creating claims in the graph."""
        mock_driver = Mock()
        mock_driver_class.return_value = mock_driver
        mock_session = Mock()
        mock_driver.session.return_value.__enter__.return_value = mock_session
        
        manager = Neo4jGraphManager(config=mock_config)
        
        claim_inputs = [
            ClaimInput(
                text="Test claim for Neo4j",
                block_id="blk_neo4j_test",
                entailed_score=0.95,
            )
        ]
        
        # Mock the session.run return value
        mock_result = Mock()
        mock_result.data.return_value = [
            {
                'claim': {
                    'id': 'claim_test123',
                    'text': 'Test claim for Neo4j',
                    'entailed_score': 0.95,
                    'version': 1,
                    'timestamp': '2024-01-01T10:00:00Z'
                }
            }
        ]
        mock_session.run.return_value = mock_result
        
        results = manager.create_claims(claim_inputs)
        assert isinstance(results, list)
        if results:
            assert isinstance(results[0], Claim)

    @patch('clarifai_shared.graph.neo4j_manager.GraphDatabase.driver')
    def test_create_sentences(self, mock_driver_class, mock_config):
        """Test creating sentences in the graph."""
        mock_driver = Mock()
        mock_driver_class.return_value = mock_driver
        mock_session = Mock()
        mock_driver.session.return_value.__enter__.return_value = mock_session
        
        manager = Neo4jGraphManager(config=mock_config)
        
        sentence_inputs = [
            SentenceInput(
                text="Test sentence for Neo4j",
                block_id="blk_neo4j_sentence_test",
                ambiguous=False,
                verifiable=True,
            )
        ]
        
        # Mock the session.run return value
        mock_result = Mock()
        mock_result.data.return_value = [
            {
                'sentence': {
                    'id': 'sentence_test123',
                    'text': 'Test sentence for Neo4j',
                    'ambiguous': False,
                    'verifiable': True,
                    'version': 1,
                    'timestamp': '2024-01-01T10:00:00Z'
                }
            }
        ]
        mock_session.run.return_value = mock_result
        
        results = manager.create_sentences(sentence_inputs)
        assert isinstance(results, list)
        if results:
            assert isinstance(results[0], Sentence)

    @patch('clarifai_shared.graph.neo4j_manager.GraphDatabase.driver')
    def test_get_claim_by_id(self, mock_driver_class, mock_config):
        """Test retrieving a claim by ID."""
        mock_driver = Mock()
        mock_driver_class.return_value = mock_driver
        mock_session = Mock()
        mock_driver.session.return_value.__enter__.return_value = mock_session
        
        manager = Neo4jGraphManager(config=mock_config)
        
        # Mock successful result
        mock_result = Mock()
        mock_result.single.return_value = {
            'claim': {
                'id': 'claim_test123',
                'text': 'Test claim',
                'version': 1,
                'timestamp': '2024-01-01T10:00:00Z'
            }
        }
        mock_session.run.return_value = mock_result
        
        claim = manager.get_claim_by_id("claim_test123")
        assert claim is not None
        assert isinstance(claim, dict)

    @patch('clarifai_shared.graph.neo4j_manager.GraphDatabase.driver')
    def test_get_sentence_by_id(self, mock_driver_class, mock_config):
        """Test retrieving a sentence by ID."""
        mock_driver = Mock()
        mock_driver_class.return_value = mock_driver
        mock_session = Mock()
        mock_driver.session.return_value.__enter__.return_value = mock_session
        
        manager = Neo4jGraphManager(config=mock_config)
        
        # Mock successful result
        mock_result = Mock()
        mock_result.single.return_value = {
            'sentence': {
                'id': 'sentence_test123',
                'text': 'Test sentence',
                'version': 1,
                'timestamp': '2024-01-01T10:00:00Z'
            }
        }
        mock_session.run.return_value = mock_result
        
        sentence = manager.get_sentence_by_id("sentence_test123")
        assert sentence is not None
        assert isinstance(sentence, dict)

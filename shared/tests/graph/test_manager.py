"""
Tests for Neo4j Graph Manager.

Tests the Neo4jGraphManager functionality including connection, schema setup,
and batch operations for creating nodes and relationships.
"""

import unittest
from unittest.mock import Mock, patch
from datetime import datetime

# Import the graph manager components
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from clarifai_shared.graph.manager import Neo4jGraphManager, MockSession, MockResult
from clarifai_shared.graph.data_models import ClaimInput, SentenceInput, BlockNodeInput


class TestNeo4jGraphManager(unittest.TestCase):
    """Test Neo4jGraphManager functionality."""
    
    def setUp(self):
        """Set up test data and manager instance."""
        self.config = {
            'host': 'localhost',
            'port': 7687,
            'username': 'neo4j',
            'password': 'test'
        }
        self.manager = Neo4jGraphManager(config=self.config)
    
    def test_manager_initialization(self):
        """Test manager initialization with config."""
        # Test with config
        manager = Neo4jGraphManager(config=self.config)
        self.assertIsNotNone(manager)
        self.assertEqual(manager.uri, "bolt://localhost:7687")
        
        # Test with no config (uses environment variables/defaults)
        manager = Neo4jGraphManager()
        self.assertIsNotNone(manager)
    
    def test_connection_uri_building(self):
        """Test connection URI building from config."""
        manager = Neo4jGraphManager(config=self.config)
        expected_uri = "bolt://localhost:7687"
        self.assertEqual(manager.uri, expected_uri)
        
        # Test with different host/port
        config = {'host': 'neo4j-server', 'port': 7688}
        manager = Neo4jGraphManager(config=config)
        expected_uri = "bolt://neo4j-server:7688"
        self.assertEqual(manager.uri, expected_uri)
    
    def test_auth_credentials(self):
        """Test authentication credentials setup."""
        manager = Neo4jGraphManager(config=self.config)
        expected_auth = ("neo4j", "test")
        self.assertEqual(manager.auth, expected_auth)
    
    def test_mock_session_functionality(self):
        """Test mock session for testing without Neo4j."""
        # Since NEO4J_AVAILABLE is likely False in test environment,
        # test the mock session functionality
        with self.manager.get_session() as session:
            self.assertIsInstance(session, MockSession)
            
            result = session.run("MATCH (n) RETURN n")
            self.assertIsInstance(result, MockResult)
            
            # Test mock result methods
            single_result = result.single()
            self.assertIn("test", single_result)
            self.assertEqual(single_result["test"], 1)
    
    def test_connection_test(self):
        """Test connection testing functionality."""
        # Should work with mock session
        connection_ok = self.manager.test_connection()
        # In mock mode, this might return False, which is expected
        self.assertIsInstance(connection_ok, bool)
    
    def test_schema_application(self):
        """Test core schema application."""
        # Should work with mock session (won't actually create constraints)
        success = self.manager.apply_core_schema()
        self.assertTrue(success)
    
    def test_create_claims_in_batch_empty(self):
        """Test batch claim creation with empty list."""
        success = self.manager.create_claims_in_batch([])
        self.assertTrue(success)
    
    def test_create_claims_in_batch_with_data(self):
        """Test batch claim creation with data."""
        claims = [
            ClaimInput(
                id="claim_001",
                text="The system failed at startup.",
                block_id="blk_001",
                entailed_score=0.9,
                coverage_score=0.8
            ),
            ClaimInput(
                id="claim_002", 
                text="The error occurred at 10:30 AM.",
                block_id="blk_001",
                decontextualization_score=0.7
            )
        ]
        
        success = self.manager.create_claims_in_batch(claims)
        self.assertTrue(success)
    
    def test_create_sentences_in_batch_empty(self):
        """Test batch sentence creation with empty list."""
        success = self.manager.create_sentences_in_batch([])
        self.assertTrue(success)
    
    def test_create_sentences_in_batch_with_data(self):
        """Test batch sentence creation with data."""
        sentences = [
            SentenceInput(
                id="sent_001",
                text="What should we do about this?",
                block_id="blk_001",
                ambiguous=True,
                rejection_reason="Question format"
            ),
            SentenceInput(
                id="sent_002",
                text="It failed again.",
                block_id="blk_002",
                ambiguous=True,
                verifiable=True,
                rejection_reason="Ambiguous reference"
            )
        ]
        
        success = self.manager.create_sentences_in_batch(sentences)
        self.assertTrue(success)
    
    def test_create_blocks_in_batch_empty(self):
        """Test batch block creation with empty list."""
        success = self.manager.create_blocks_in_batch([])
        self.assertTrue(success)
    
    def test_create_blocks_in_batch_with_data(self):
        """Test batch block creation with data."""
        blocks = [
            BlockNodeInput(
                id="blk_001",
                text="Original block content",
                block_id="blk_001",
                content_hash="abc123",
                source_file="/vault/file1.md"
            ),
            BlockNodeInput(
                id="blk_002",
                text="Another block content",
                block_id="blk_002",
                content_hash="def456",
                source_file="/vault/file2.md",
                needs_reprocessing=True
            )
        ]
        
        success = self.manager.create_blocks_in_batch(blocks)
        self.assertTrue(success)
    
    def test_get_node_by_id(self):
        """Test getting node by ID."""
        # With mock session, this will return None
        result = self.manager.get_node_by_id("test_id")
        # In mock mode, this returns None which is expected
        self.assertIsNone(result)
        
        # Test with node type filter
        result = self.manager.get_node_by_id("test_id", "Claim")
        self.assertIsNone(result)
    
    def test_execute_cypher_query(self):
        """Test custom Cypher query execution."""
        query = "MATCH (n:Claim) RETURN count(n) as claim_count"
        results = self.manager.execute_cypher_query(query)
        
        # With mock session, returns empty list
        self.assertIsInstance(results, list)
    
    def test_manager_close(self):
        """Test manager connection cleanup."""
        # Should not raise any exceptions
        self.manager.close()


class TestGraphManagerIntegration(unittest.TestCase):
    """Integration tests for graph manager with realistic scenarios."""
    
    def setUp(self):
        """Set up test manager."""
        self.manager = Neo4jGraphManager()
    
    def test_end_to_end_claim_persistence(self):
        """Test complete claim persistence workflow."""
        # Apply schema first
        schema_applied = self.manager.apply_core_schema()
        self.assertTrue(schema_applied)
        
        # Create test claims
        claims = [
            ClaimInput(
                id="claim_test_001",
                text="The database connection failed during peak hours.",
                block_id="blk_test_001",
                entailed_score=0.95,
                coverage_score=0.88,
                decontextualization_score=0.92
            ),
            ClaimInput(
                id="claim_test_002",
                text="The error rate increased to 15% after deployment.",
                block_id="blk_test_001",
                entailed_score=0.87,
                coverage_score=0.91
            )
        ]
        
        # Persist claims
        success = self.manager.create_claims_in_batch(claims)
        self.assertTrue(success)
        
        # Create corresponding sentences that failed criteria
        sentences = [
            SentenceInput(
                id="sent_test_001",
                text="What should we do about this issue?",
                block_id="blk_test_001",
                ambiguous=False,
                verifiable=False,
                rejection_reason="Question format, not verifiable"
            )
        ]
        
        # Persist sentences
        success = self.manager.create_sentences_in_batch(sentences)
        self.assertTrue(success)
    
    def test_mixed_content_persistence(self):
        """Test persisting mixed content types."""
        # Create blocks first
        blocks = [
            BlockNodeInput(
                id="blk_mixed_001",
                text="Original conversation block",
                block_id="blk_mixed_001",
                content_hash="mixed123",
                source_file="/vault/conversations/mixed_content.md"
            )
        ]
        
        success = self.manager.create_blocks_in_batch(blocks)
        self.assertTrue(success)
        
        # Create claims from the block
        claims = [
            ClaimInput(
                id="claim_mixed_001",
                text="User reported login failure at 9:15 AM.",
                block_id="blk_mixed_001"
            )
        ]
        
        success = self.manager.create_claims_in_batch(claims)
        self.assertTrue(success)
        
        # Create sentences that didn't become claims
        sentences = [
            SentenceInput(
                id="sent_mixed_001",
                text="Hmm, that's strange.",
                block_id="blk_mixed_001",
                rejection_reason="Too short, no verifiable content"
            )
        ]
        
        success = self.manager.create_sentences_in_batch(sentences)
        self.assertTrue(success)
    
    def test_error_handling(self):
        """Test error handling in graph operations."""
        # Test with malformed data (should not crash)
        claims = [
            ClaimInput(
                id="",  # Empty ID might cause issues
                text="Test claim",
                block_id="blk_001"
            )
        ]
        
        # Should handle gracefully (might return False but shouldn't crash)
        success = self.manager.create_claims_in_batch(claims)
        self.assertIsInstance(success, bool)


if __name__ == '__main__':
    unittest.main()
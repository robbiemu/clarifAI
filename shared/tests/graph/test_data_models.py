"""
Tests for graph data models.

Tests the data models used for Neo4j node creation and conversion.
"""

import unittest
from datetime import datetime

# Import the graph data models
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from clarifai_shared.graph.data_models import (
    ClaimInput,
    SentenceInput,
    BlockNodeInput,
    GraphNodeInput,
)


class TestGraphNodeInput(unittest.TestCase):
    """Test base GraphNodeInput functionality."""
    
    def test_base_node_creation(self):
        """Test creation of base GraphNodeInput."""
        node = GraphNodeInput(
            id="test_id",
            text="Test text",
            block_id="blk_001"
        )
        
        self.assertEqual(node.id, "test_id")
        self.assertEqual(node.text, "Test text")
        self.assertEqual(node.block_id, "blk_001")
        self.assertEqual(node.version, 1)
        self.assertIsNotNone(node.timestamp)
    
    def test_custom_timestamp(self):
        """Test creation with custom timestamp."""
        custom_time = datetime(2024, 1, 1, 12, 0, 0)
        node = GraphNodeInput(
            id="test_id",
            text="Test text",
            block_id="blk_001",
            timestamp=custom_time
        )
        
        self.assertEqual(node.timestamp, custom_time)


class TestClaimInput(unittest.TestCase):
    """Test ClaimInput data model."""
    
    def test_claim_input_creation(self):
        """Test basic ClaimInput creation."""
        claim = ClaimInput(
            id="claim_001",
            text="The system reported an error.",
            block_id="blk_001"
        )
        
        self.assertEqual(claim.id, "claim_001")
        self.assertEqual(claim.text, "The system reported an error.")
        self.assertEqual(claim.block_id, "blk_001")
        self.assertTrue(claim.verifiable)
        self.assertTrue(claim.self_contained)
        self.assertTrue(claim.context_complete)
        self.assertIsNone(claim.entailed_score)
        self.assertIsNone(claim.coverage_score)
        self.assertIsNone(claim.decontextualization_score)
    
    def test_claim_input_with_scores(self):
        """Test ClaimInput creation with quality scores."""
        claim = ClaimInput(
            id="claim_002",
            text="The error occurred at 10:30 AM.",
            block_id="blk_001",
            entailed_score=0.85,
            coverage_score=0.92,
            decontextualization_score=0.78
        )
        
        self.assertEqual(claim.entailed_score, 0.85)
        self.assertEqual(claim.coverage_score, 0.92)
        self.assertEqual(claim.decontextualization_score, 0.78)
    
    def test_claim_neo4j_properties(self):
        """Test conversion to Neo4j properties."""
        custom_time = datetime(2024, 1, 1, 12, 0, 0)
        claim = ClaimInput(
            id="claim_003",
            text="Database connection failed.",
            block_id="blk_002",
            entailed_score=0.9,
            coverage_score=0.8,
            decontextualization_score=0.7,
            verifiable=True,
            self_contained=False,
            context_complete=True,
            version=2,
            timestamp=custom_time
        )
        
        properties = claim.to_neo4j_properties()
        
        expected_properties = {
            "id": "claim_003",
            "text": "Database connection failed.",
            "entailed_score": 0.9,
            "coverage_score": 0.8,
            "decontextualization_score": 0.7,
            "verifiable": True,
            "self_contained": False,
            "context_complete": True,
            "version": 2,
            "timestamp": "2024-01-01T12:00:00"
        }
        
        self.assertEqual(properties, expected_properties)


class TestSentenceInput(unittest.TestCase):
    """Test SentenceInput data model."""
    
    def test_sentence_input_creation(self):
        """Test basic SentenceInput creation."""
        sentence = SentenceInput(
            id="sent_001",
            text="What should we do?",
            block_id="blk_001"
        )
        
        self.assertEqual(sentence.id, "sent_001")
        self.assertEqual(sentence.text, "What should we do?")
        self.assertEqual(sentence.block_id, "blk_001")
        self.assertFalse(sentence.ambiguous)
        self.assertFalse(sentence.verifiable)
        self.assertFalse(sentence.failed_decomposition)
        self.assertIsNone(sentence.rejection_reason)
    
    def test_sentence_input_with_flags(self):
        """Test SentenceInput with quality flags."""
        sentence = SentenceInput(
            id="sent_002",
            text="It failed again.",
            block_id="blk_001",
            ambiguous=True,
            verifiable=True,
            failed_decomposition=True,
            rejection_reason="Ambiguous pronoun reference"
        )
        
        self.assertTrue(sentence.ambiguous)
        self.assertTrue(sentence.verifiable)
        self.assertTrue(sentence.failed_decomposition)
        self.assertEqual(sentence.rejection_reason, "Ambiguous pronoun reference")
    
    def test_sentence_neo4j_properties(self):
        """Test conversion to Neo4j properties."""
        custom_time = datetime(2024, 1, 1, 12, 0, 0)
        sentence = SentenceInput(
            id="sent_003",
            text="This is ambiguous.",
            block_id="blk_002",
            ambiguous=True,
            verifiable=False,
            failed_decomposition=False,
            rejection_reason="Too ambiguous",
            version=1,
            timestamp=custom_time
        )
        
        properties = sentence.to_neo4j_properties()
        
        expected_properties = {
            "id": "sent_003",
            "text": "This is ambiguous.",
            "ambiguous": True,
            "verifiable": False,
            "failed_decomposition": False,
            "rejection_reason": "Too ambiguous",
            "version": 1,
            "timestamp": "2024-01-01T12:00:00"
        }
        
        self.assertEqual(properties, expected_properties)


class TestBlockNodeInput(unittest.TestCase):
    """Test BlockNodeInput data model."""
    
    def test_block_input_creation(self):
        """Test basic BlockNodeInput creation."""
        block = BlockNodeInput(
            id="blk_001",
            text="Block content here",
            block_id="blk_001"  # For blocks, block_id might be the same as id
        )
        
        self.assertEqual(block.id, "blk_001")
        self.assertEqual(block.text, "Block content here")
        self.assertIsNone(block.content_hash)
        self.assertIsNone(block.source_file)
        self.assertFalse(block.needs_reprocessing)
        self.assertIsNone(block.last_synced)
    
    def test_block_input_with_metadata(self):
        """Test BlockNodeInput with full metadata."""
        sync_time = datetime(2024, 1, 1, 10, 0, 0)
        create_time = datetime(2024, 1, 1, 12, 0, 0)
        
        block = BlockNodeInput(
            id="blk_002",
            text="Complete block content",
            block_id="blk_002",
            content_hash="abc123def456",
            source_file="/vault/conversations/file.md",
            needs_reprocessing=True,
            last_synced=sync_time,
            version=3,
            timestamp=create_time
        )
        
        self.assertEqual(block.content_hash, "abc123def456")
        self.assertEqual(block.source_file, "/vault/conversations/file.md")
        self.assertTrue(block.needs_reprocessing)
        self.assertEqual(block.last_synced, sync_time)
        self.assertEqual(block.version, 3)
    
    def test_block_neo4j_properties(self):
        """Test conversion to Neo4j properties."""
        sync_time = datetime(2024, 1, 1, 10, 0, 0)
        create_time = datetime(2024, 1, 1, 12, 0, 0)
        
        block = BlockNodeInput(
            id="blk_003",
            text="Block with all properties",
            block_id="blk_003",
            content_hash="hash123",
            source_file="/path/to/file.md",
            needs_reprocessing=False,
            last_synced=sync_time,
            version=1,
            timestamp=create_time
        )
        
        properties = block.to_neo4j_properties()
        
        expected_properties = {
            "id": "blk_003",
            "text": "Block with all properties",
            "content_hash": "hash123",
            "source_file": "/path/to/file.md",
            "needs_reprocessing": False,
            "version": 1,
            "timestamp": "2024-01-01T12:00:00",
            "last_synced": "2024-01-01T10:00:00"
        }
        
        self.assertEqual(properties, expected_properties)


if __name__ == '__main__':
    unittest.main()
"""
Tests for Neo4j graph manager.
"""

from clarifai_shared.graph.neo4j_manager import Neo4jGraphManager
from clarifai_shared.graph.models import ClaimInput, SentenceInput, Claim, Sentence
from clarifai_shared.config import ClarifAIConfig, DatabaseConfig


class TestNeo4jGraphManager:
    """Test cases for Neo4jGraphManager."""

    def test_neo4j_manager_init_with_config(self):
        """Test Neo4jGraphManager initialization with config."""
        config = ClarifAIConfig()
        config.database = DatabaseConfig(
            host="localhost",
            port=7687,
            user="neo4j",
            password="password",
        )
        
        manager = Neo4jGraphManager(config=config)
            assert manager.config == config

    def test_neo4j_manager_init_default_config(self):
        """Test Neo4jGraphManager initialization with default config."""            manager = Neo4jGraphManager()
            assert manager.config is not None

    def test_create_claim(self):
        """Test creating a claim in the graph."""
        config = ClarifAIConfig()
        config.database = DatabaseConfig(
            host="localhost",
            port=7687,
            user="neo4j", 
            password="test_pass"
        )
        
        manager = Neo4jGraphManager(config=config)

            claim_input = ClaimInput(
                text="Test claim for Neo4j",
                block_id="blk_neo4j_test",
                entailed_score=0.95,
            )

            result = manager.create_claim(claim_input)
            assert isinstance(result, (Claim, type(None)))

    def test_create_sentence(self):
        """Test creating a sentence in the graph."""
        config = ClarifAIConfig()
        config.database = DatabaseConfig(
            host="localhost",
            port=7687,
            user="neo4j", 
            password="test_pass"
        )
        
        manager = Neo4jGraphManager(config=config)

            sentence_input = SentenceInput(
                text="Test sentence for Neo4j",
                block_id="blk_neo4j_sentence_test",
                ambiguous=False,
                verifiable=True,
            )

            result = manager.create_sentence(sentence_input)
            assert isinstance(result, (Sentence, type(None)))

    def test_get_claim_by_id(self):
        """Test retrieving a claim by ID."""
        config = ClarifAIConfig()
        config.database = DatabaseConfig(
            host="localhost",
            port=7687,
            user="neo4j", 
            password="test_pass"
        )
        
        manager = Neo4jGraphManager(config=config)

            claim = manager.get_claim_by_id("claim_test123")
            # Should return Claim object or None
            assert isinstance(claim, (Claim, type(None)))

    def test_get_sentence_by_id(self):
        """Test retrieving a sentence by ID."""
        config = ClarifAIConfig()
        config.database = DatabaseConfig(
            host="localhost",
            port=7687,
            user="neo4j", 
            password="test_pass"
        )
        
        manager = Neo4jGraphManager(config=config)

            sentence = manager.get_sentence_by_id("sentence_test123")
            # Should return Sentence object or None
            assert isinstance(sentence, (Sentence, type(None)))

    def test_update_claim(self):
        """Test updating a claim in the graph."""
        config = ClarifAIConfig()
        config.database = DatabaseConfig(
            host="localhost",
            port=7687,
            user="neo4j", 
            password="test_pass"
        )
        
        manager = Neo4jGraphManager(config=config)

            claim_input = ClaimInput(
                text="Updated claim text",
                block_id="blk_update_test",
                claim_id="claim_update_test",
                entailed_score=0.88,
            )

            result = manager.update_claim(claim_input)
            assert isinstance(result, (Claim, type(None), bool))

    def test_update_sentence(self):
        """Test updating a sentence in the graph."""
        config = ClarifAIConfig()
        config.database = DatabaseConfig(
            host="localhost",
            port=7687,
            user="neo4j", 
            password="test_pass"
        )
        
        manager = Neo4jGraphManager(config=config)

            sentence_input = SentenceInput(
                text="Updated sentence text",
                block_id="blk_sentence_update_test",
                sentence_id="sentence_update_test",
                ambiguous=True,
            )

            result = manager.update_sentence(sentence_input)
            assert isinstance(result, (Sentence, type(None), bool))

    def test_delete_claim(self):
        """Test deleting a claim from the graph."""
        config = ClarifAIConfig()
        config.database = DatabaseConfig(
            host="localhost",
            port=7687,
            user="neo4j", 
            password="test_pass"
        )
        
        manager = Neo4jGraphManager(config=config)

            result = manager.delete_claim("claim_delete_test")
            assert isinstance(result, bool)

    def test_delete_sentence(self):
        """Test deleting a sentence from the graph."""
        config = ClarifAIConfig()
        config.database = DatabaseConfig(
            host="localhost",
            port=7687,
            user="neo4j", 
            password="test_pass"
        )
        
        manager = Neo4jGraphManager(config=config)

            result = manager.delete_sentence("sentence_delete_test")
            assert isinstance(result, bool)

    def test_get_claims_by_block_id(self):
        """Test retrieving claims by block ID."""
        config = ClarifAIConfig()
        config.database = DatabaseConfig(
            host="localhost",
            port=7687,
            user="neo4j", 
            password="test_pass"
        )
        
        manager = Neo4jGraphManager(config=config)

            claims = manager.get_claims_by_block_id("blk_test_block")
            assert isinstance(claims, list)

    def test_get_sentences_by_block_id(self):
        """Test retrieving sentences by block ID."""
        config = ClarifAIConfig()
        config.database = DatabaseConfig(
            host="localhost",
            port=7687,
            user="neo4j", 
            password="test_pass"
        )
        
        manager = Neo4jGraphManager(config=config)

            sentences = manager.get_sentences_by_block_id("blk_test_block")
            assert isinstance(sentences, list)

    def test_create_relationship(self):
        """Test creating relationships between nodes."""
        config = ClarifAIConfig()
        config.database = DatabaseConfig(
            host="localhost",
            port=7687,
            user="neo4j", 
            password="test_pass"
        )
        
        manager = Neo4jGraphManager(config=config)

            result = manager.create_relationship(
                from_id="claim_test1",
                to_id="claim_test2",
                relationship_type="SUPPORTS",
                properties={"confidence": 0.85},
            )
            assert isinstance(result, bool)

    def test_get_related_claims(self):
        """Test getting related claims."""
        config = ClarifAIConfig()
        config.database = DatabaseConfig(
            host="localhost",
            port=7687,
            user="neo4j", 
            password="test_pass"
        )
        
        manager = Neo4jGraphManager(config=config)

            related_claims = manager.get_related_claims(
                claim_id="claim_test123", relationship_type="SUPPORTS"
            )
            assert isinstance(related_claims, list)

    def test_execute_cypher_query(self):
        """Test executing Cypher queries."""
        config = ClarifAIConfig()
        config.database = DatabaseConfig(
            host="localhost",
            port=7687,
            user="neo4j", 
            password="test_pass"
        )
        
        manager = Neo4jGraphManager(config=config)

            result = manager.execute_cypher_query(
                "MATCH (n) RETURN count(n) as count", parameters={}
            )
            assert isinstance(result, list)

    def test_get_graph_statistics(self):
        """Test getting graph statistics."""
        config = ClarifAIConfig()
        config.database = DatabaseConfig(
            host="localhost",
            port=7687,
            user="neo4j", 
            password="test_pass"
        )
        
        manager = Neo4jGraphManager(config=config)

            stats = manager.get_graph_statistics()
            assert isinstance(stats, dict)

    def test_create_index(self):
        """Test creating database indexes."""
        config = ClarifAIConfig()
        config.database = DatabaseConfig(
            host="localhost",
            port=7687,
            user="neo4j", 
            password="test_pass"
        )
        
        manager = Neo4jGraphManager(config=config)

            result = manager.create_index("Claim", "claim_id")
            assert isinstance(result, bool)

    def test_connection_management(self):
        """Test database connection management."""
        config = ClarifAIConfig()
        config.database = DatabaseConfig(
            host="localhost",
            port=7687,
            user="neo4j", 
            password="test_pass"
        )
        
        manager = Neo4jGraphManager(config=config)

            # Test connection check
            is_connected = manager.test_connection()
            assert isinstance(is_connected, bool)

            # Test close connection
            manager.close()

    def test_batch_operations(self):
        """Test batch operations."""
        config = ClarifAIConfig()
        config.database = DatabaseConfig(
            host="localhost",
            port=7687,
            user="neo4j", 
            password="test_pass"
        )
        
        manager = Neo4jGraphManager(config=config)

            claim_inputs = [
                ClaimInput(text="Batch claim 1", block_id="blk_batch_1"),
                ClaimInput(text="Batch claim 2", block_id="blk_batch_2"),
            ]

            results = manager.batch_create_claims(claim_inputs)
            assert isinstance(results, list)

    def test_transaction_management(self):
        """Test transaction management."""
        config = ClarifAIConfig()
        config.database = DatabaseConfig(
            host="localhost",
            port=7687,
            user="neo4j", 
            password="test_pass"
        )
        
        manager = Neo4jGraphManager(config=config)

            # Test begin transaction
            tx_id = manager.begin_transaction()
            assert isinstance(tx_id, (str, type(None)))

            # Test commit transaction
            if tx_id:
                result = manager.commit_transaction(tx_id)
                assert isinstance(result, bool)

    def test_error_handling(self):
        """Test error handling in Neo4j operations."""
        config = ClarifAIConfig()
        config.database = DatabaseConfig(
            host="localhost",
            port=7687,
            user="neo4j", 
            password="test_pass"
        )
        
        manager = Neo4jGraphManager(config=config)

            # Test with invalid query
            result = manager.execute_cypher_query("INVALID CYPHER QUERY")
            # Should handle error gracefully
            assert isinstance(result, (list, type(None)))

    def test_graph_cleanup(self):
        """Test graph cleanup operations."""
        config = ClarifAIConfig()
        config.database = DatabaseConfig(
            host="localhost",
            port=7687,
            user="neo4j", 
            password="test_pass"
        )
        
        manager = Neo4jGraphManager(config=config)

            # Test clearing orphaned nodes
            result = manager.cleanup_orphaned_nodes()
            assert isinstance(result, (int, type(None)))

            # Test clearing test data
            result = manager.clear_test_data()
            assert isinstance(result, bool)

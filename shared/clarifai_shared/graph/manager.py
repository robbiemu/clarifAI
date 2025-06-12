"""
Neo4j Graph Manager for ClarifAI.

Provides the core Neo4j interaction functionality required by the Claimify pipeline
and other graph-based components. Implements direct Cypher queries for precise
control over node creation, relationships, and batch operations.
"""

import logging
from typing import List, Optional, Dict, Any, Union
from contextlib import contextmanager
import os

from .data_models import ClaimInput, SentenceInput, BlockNodeInput, NodeInputType

logger = logging.getLogger(__name__)

# This is a placeholder for the Neo4j driver import
# In a real implementation, you would install neo4j: pip install neo4j
try:
    from neo4j import GraphDatabase, Session
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    logger.warning("Neo4j driver not available. Graph operations will be mocked.")


class Neo4jGraphManager:
    """
    Manages Neo4j graph operations for ClarifAI.
    
    Provides methods for creating nodes, relationships, and managing the graph schema
    as required by Sprint 3 tasks. Uses direct Cypher queries for optimal performance
    and precise control.
    
    Based on the architecture defined in idea-neo4J-ineteraction.md.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Neo4j Graph Manager.
        
        Args:
            config: Configuration dictionary with Neo4j connection details.
                   If None, will use environment variables.
        """
        self.config = config or {}
        self._driver = None
        self._is_connected = False
        
        # Connection configuration
        self.uri = self._get_connection_uri()
        self.auth = self._get_auth_credentials()
        
        # Initialize connection if Neo4j is available
        if NEO4J_AVAILABLE:
            self._initialize_connection()
        else:
            logger.warning("[manager.Neo4jGraphManager.__init__] Running in mock mode")
    
    def _get_connection_uri(self) -> str:
        """Get Neo4j connection URI from config or environment."""
        if 'uri' in self.config:
            return self.config['uri']
        
        # Build from host/port configuration
        host = self.config.get('host', os.getenv('NEO4J_HOST', 'neo4j'))
        port = self.config.get('port', int(os.getenv('NEO4J_BOLT_PORT', '7687')))
        
        return f"bolt://{host}:{port}"
    
    def _get_auth_credentials(self) -> tuple:
        """Get Neo4j authentication credentials."""
        username = self.config.get('username', os.getenv('NEO4J_USER', 'neo4j'))
        password = self.config.get('password', os.getenv('NEO4J_PASSWORD', 'password'))
        
        return (username, password)
    
    def _initialize_connection(self):
        """Initialize the Neo4j driver connection."""
        try:
            self._driver = GraphDatabase.driver(self.uri, auth=self.auth)
            self._driver.verify_connectivity()
            self._is_connected = True
            logger.info(f"[manager.Neo4jGraphManager._initialize_connection] Connected to Neo4j at {self.uri}")
        except Exception as e:
            logger.error(f"[manager.Neo4jGraphManager._initialize_connection] Failed to connect to Neo4j: {e}")
            self._is_connected = False
    
    @contextmanager
    def get_session(self):
        """Get a Neo4j session for database operations."""
        if not NEO4J_AVAILABLE or not self._is_connected:
            # Mock session for testing/development
            yield MockSession()
            return
            
        with self._driver.session() as session:
            yield session
    
    def close(self):
        """Close the Neo4j driver connection."""
        if self._driver:
            self._driver.close()
            self._is_connected = False
            logger.info("[manager.Neo4jGraphManager.close] Neo4j connection closed")
    
    def test_connection(self) -> bool:
        """Test the Neo4j connection."""
        if not NEO4J_AVAILABLE:
            logger.warning("[manager.Neo4jGraphManager.test_connection] Neo4j driver not available")
            return False
            
        try:
            with self.get_session() as session:
                result = session.run("RETURN 1 as test")
                test_value = result.single()["test"]
                success = test_value == 1
                
                if success:
                    logger.info("[manager.Neo4jGraphManager.test_connection] Connection test successful")
                else:
                    logger.error("[manager.Neo4jGraphManager.test_connection] Connection test failed")
                    
                return success
        except Exception as e:
            logger.error(f"[manager.Neo4jGraphManager.test_connection] Connection test failed: {e}")
            return False
    
    def apply_core_schema(self) -> bool:
        """
        Apply the core graph schema for ClarifAI.
        
        Creates constraints and indexes for Claim, Sentence, and Block nodes
        as defined in graph_schema.cypher.
        
        Returns:
            bool: True if schema was applied successfully
        """
        schema_queries = [
            # Constraints for unique IDs
            "CREATE CONSTRAINT claim_id_unique IF NOT EXISTS FOR (c:Claim) REQUIRE c.id IS UNIQUE",
            "CREATE CONSTRAINT sentence_id_unique IF NOT EXISTS FOR (s:Sentence) REQUIRE s.id IS UNIQUE", 
            "CREATE CONSTRAINT block_id_unique IF NOT EXISTS FOR (b:Block) REQUIRE b.id IS UNIQUE",
            
            # Indexes for performance
            "CREATE INDEX claim_verifiable_idx IF NOT EXISTS FOR (c:Claim) ON (c.verifiable)",
            "CREATE INDEX claim_entailed_score_idx IF NOT EXISTS FOR (c:Claim) ON (c.entailed_score)",
            "CREATE INDEX sentence_ambiguous_idx IF NOT EXISTS FOR (s:Sentence) ON (s.ambiguous)",
            "CREATE INDEX block_hash_idx IF NOT EXISTS FOR (b:Block) ON (b.content_hash)",
        ]
        
        try:
            with self.get_session() as session:
                for query in schema_queries:
                    session.run(query)
                    logger.debug(f"[manager.Neo4jGraphManager.apply_core_schema] Applied: {query}")
                
                logger.info("[manager.Neo4jGraphManager.apply_core_schema] Core schema applied successfully")
                return True
                
        except Exception as e:
            logger.error(f"[manager.Neo4jGraphManager.apply_core_schema] Failed to apply schema: {e}")
            return False
    
    def create_claims_in_batch(self, claim_inputs: List[ClaimInput]) -> bool:
        """
        Create Claim nodes in batch with ORIGINATES_FROM relationships.
        
        Args:
            claim_inputs: List of ClaimInput objects to create
            
        Returns:
            bool: True if all claims were created successfully
        """
        if not claim_inputs:
            logger.info("[manager.Neo4jGraphManager.create_claims_in_batch] No claims to create")
            return True
        
        # Prepare data for UNWIND batch operation
        claims_data = [claim.to_neo4j_properties() for claim in claim_inputs]
        
        cypher_query = """
        UNWIND $claims_data AS claim_data
        MERGE (c:Claim {id: claim_data.id})
        ON CREATE SET
            c.text = claim_data.text,
            c.entailed_score = claim_data.entailed_score,
            c.coverage_score = claim_data.coverage_score,
            c.decontextualization_score = claim_data.decontextualization_score,
            c.verifiable = claim_data.verifiable,
            c.self_contained = claim_data.self_contained,
            c.context_complete = claim_data.context_complete,
            c.version = claim_data.version,
            c.timestamp = datetime(claim_data.timestamp)
        MERGE (b:Block {id: $block_id})
        ON CREATE SET
            b.version = 1,
            b.timestamp = datetime()
        MERGE (c)-[:ORIGINATES_FROM]->(b)
        RETURN count(c) as created_claims
        """
        
        try:
            with self.get_session() as session:
                # Group claims by block_id for efficient processing
                claims_by_block = {}
                for claim in claim_inputs:
                    block_id = claim.block_id
                    if block_id not in claims_by_block:
                        claims_by_block[block_id] = []
                    claims_by_block[block_id].append(claim.to_neo4j_properties())
                
                total_created = 0
                for block_id, block_claims in claims_by_block.items():
                    result = session.run(cypher_query, {
                        'claims_data': block_claims,
                        'block_id': block_id
                    })
                    created_count = result.single()["created_claims"]
                    total_created += created_count
                
                logger.info(f"[manager.Neo4jGraphManager.create_claims_in_batch] Created {total_created} claim nodes")
                return True
                
        except Exception as e:
            logger.error(f"[manager.Neo4jGraphManager.create_claims_in_batch] Failed to create claims: {e}")
            return False
    
    def create_sentences_in_batch(self, sentence_inputs: List[SentenceInput]) -> bool:
        """
        Create Sentence nodes in batch with ORIGINATES_FROM relationships.
        
        Args:
            sentence_inputs: List of SentenceInput objects to create
            
        Returns:
            bool: True if all sentences were created successfully
        """
        if not sentence_inputs:
            logger.info("[manager.Neo4jGraphManager.create_sentences_in_batch] No sentences to create")
            return True
        
        # Prepare data for UNWIND batch operation
        sentences_data = [sentence.to_neo4j_properties() for sentence in sentence_inputs]
        
        cypher_query = """
        UNWIND $sentences_data AS sentence_data
        MERGE (s:Sentence {id: sentence_data.id})
        ON CREATE SET
            s.text = sentence_data.text,
            s.ambiguous = sentence_data.ambiguous,
            s.verifiable = sentence_data.verifiable,
            s.failed_decomposition = sentence_data.failed_decomposition,
            s.rejection_reason = sentence_data.rejection_reason,
            s.version = sentence_data.version,
            s.timestamp = datetime(sentence_data.timestamp)
        MERGE (b:Block {id: $block_id})
        ON CREATE SET
            b.version = 1,
            b.timestamp = datetime()
        MERGE (s)-[:ORIGINATES_FROM]->(b)
        RETURN count(s) as created_sentences
        """
        
        try:
            with self.get_session() as session:
                # Group sentences by block_id for efficient processing
                sentences_by_block = {}
                for sentence in sentence_inputs:
                    block_id = sentence.block_id
                    if block_id not in sentences_by_block:
                        sentences_by_block[block_id] = []
                    sentences_by_block[block_id].append(sentence.to_neo4j_properties())
                
                total_created = 0
                for block_id, block_sentences in sentences_by_block.items():
                    result = session.run(cypher_query, {
                        'sentences_data': block_sentences,
                        'block_id': block_id
                    })
                    created_count = result.single()["created_sentences"]
                    total_created += created_count
                
                logger.info(f"[manager.Neo4jGraphManager.create_sentences_in_batch] Created {total_created} sentence nodes")
                return True
                
        except Exception as e:
            logger.error(f"[manager.Neo4jGraphManager.create_sentences_in_batch] Failed to create sentences: {e}")
            return False
    
    def create_blocks_in_batch(self, block_inputs: List[BlockNodeInput]) -> bool:
        """
        Create Block nodes in batch.
        
        Args:
            block_inputs: List of BlockNodeInput objects to create
            
        Returns:
            bool: True if all blocks were created successfully
        """
        if not block_inputs:
            logger.info("[manager.Neo4jGraphManager.create_blocks_in_batch] No blocks to create")
            return True
        
        blocks_data = [block.to_neo4j_properties() for block in block_inputs]
        
        cypher_query = """
        UNWIND $blocks_data AS block_data
        MERGE (b:Block {id: block_data.id})
        ON CREATE SET
            b.text = block_data.text,
            b.content_hash = block_data.content_hash,
            b.source_file = block_data.source_file,
            b.needs_reprocessing = block_data.needs_reprocessing,
            b.version = block_data.version,
            b.timestamp = datetime(block_data.timestamp),
            b.last_synced = datetime(block_data.last_synced)
        RETURN count(b) as created_blocks
        """
        
        try:
            with self.get_session() as session:
                result = session.run(cypher_query, {'blocks_data': blocks_data})
                created_count = result.single()["created_blocks"]
                
                logger.info(f"[manager.Neo4jGraphManager.create_blocks_in_batch] Created {created_count} block nodes")
                return True
                
        except Exception as e:
            logger.error(f"[manager.Neo4jGraphManager.create_blocks_in_batch] Failed to create blocks: {e}")
            return False
    
    def get_node_by_id(self, node_id: str, node_type: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get a node by its ID.
        
        Args:
            node_id: The unique ID of the node
            node_type: Optional node label to filter by (e.g., "Claim", "Sentence", "Block")
            
        Returns:
            Dict with node properties or None if not found
        """
        if node_type:
            cypher_query = f"MATCH (n:{node_type} {{id: $node_id}}) RETURN n"
        else:
            cypher_query = "MATCH (n {id: $node_id}) RETURN n"
        
        try:
            with self.get_session() as session:
                result = session.run(cypher_query, {'node_id': node_id})
                record = result.single()
                
                if record:
                    return dict(record["n"])
                else:
                    return None
                    
        except Exception as e:
            logger.error(f"[manager.Neo4jGraphManager.get_node_by_id] Failed to get node {node_id}: {e}")
            return None
    
    def execute_cypher_query(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Execute a custom Cypher query.
        
        Args:
            query: The Cypher query to execute
            parameters: Optional parameters for the query
            
        Returns:
            List of result records as dictionaries
        """
        try:
            with self.get_session() as session:
                result = session.run(query, parameters or {})
                return [dict(record) for record in result]
                
        except Exception as e:
            logger.error(f"[manager.Neo4jGraphManager.execute_cypher_query] Query failed: {e}")
            return []


class MockSession:
    """Mock session for testing without Neo4j connection."""
    
    def run(self, query: str, parameters: Optional[Dict[str, Any]] = None):
        """Mock run method that returns a mock result."""
        logger.debug(f"[manager.MockSession.run] Mock execution: {query}")
        return MockResult()


class MockResult:
    """Mock result for testing without Neo4j connection."""
    
    def single(self):
        """Return a mock single record."""
        return {"test": 1, "created_claims": 1, "created_sentences": 1, "created_blocks": 1}
    
    def __iter__(self):
        """Return empty iterator for mock results."""
        return iter([])
"""
Neo4j Graph Manager for ClarifAI knowledge graph operations.

This module provides the main interface for creating and managing
Claim and Sentence nodes in Neo4j, following the architectural patterns
from docs/arch/idea-neo4J-ineteraction.md.
"""

import logging
from typing import List, Dict, Any, Optional
from contextlib import contextmanager

from neo4j import GraphDatabase, Driver, Session
from neo4j.exceptions import ServiceUnavailable, AuthError

from ..config import ClarifAIConfig
from .models import Claim, Sentence, ClaimInput, SentenceInput

logger = logging.getLogger(__name__)


class Neo4jGraphManager:
    """
    Manager for Neo4j graph operations following ClarifAI architecture.
    
    Handles creation of Claim and Sentence nodes with proper relationships
    and indexing as specified in the technical requirements.
    """
    
    def __init__(self, config: Optional[ClarifAIConfig] = None):
        """
        Initialize Neo4j connection.
        
        Args:
            config: ClarifAI configuration (loads default if None)
        """
        if config is None:
            from ..config import load_config
            config = load_config(validate=False)
        
        self.config = config
        self._driver: Optional[Driver] = None
        
        # Connection details
        self.uri = config.neo4j.get_neo4j_bolt_url()
        self.auth = (config.neo4j.user, config.neo4j.password)
        
        logger.info(f"Initialized Neo4jGraphManager for {self.uri}")
    
    @property
    def driver(self) -> Driver:
        """Get or create Neo4j driver."""
        if self._driver is None:
            try:
                self._driver = GraphDatabase.driver(self.uri, auth=self.auth)
                self._driver.verify_connectivity()
                logger.info("Neo4j driver connected successfully")
            except (ServiceUnavailable, AuthError) as e:
                logger.error(f"Failed to connect to Neo4j: {e}")
                raise
        return self._driver
    
    def close(self):
        """Close Neo4j driver connection."""
        if self._driver is not None:
            self._driver.close()
            self._driver = None
            logger.info("Neo4j driver connection closed")
    
    @contextmanager
    def session(self):
        """Context manager for Neo4j sessions."""
        session = self.driver.session()
        try:
            yield session
        finally:
            session.close()
    
    def setup_schema(self):
        """
        Set up Neo4j schema with constraints and indexes.
        
        Creates constraints and indexes as specified in graph_schema.cypher
        and technical requirements.
        """
        schema_queries = [
            # Constraints for unique IDs
            "CREATE CONSTRAINT claim_id_unique IF NOT EXISTS FOR (c:Claim) REQUIRE c.id IS UNIQUE",
            "CREATE CONSTRAINT sentence_id_unique IF NOT EXISTS FOR (s:Sentence) REQUIRE s.id IS UNIQUE", 
            
            # Indexes for performance (technical requirements specify clarifai:id and text)
            "CREATE INDEX claim_text_index IF NOT EXISTS FOR (c:Claim) ON (c.text)",
            "CREATE INDEX sentence_text_index IF NOT EXISTS FOR (s:Sentence) ON (s.text)",
            
            # Additional performance indexes from graph_schema.cypher
            "CREATE INDEX claim_entailed_score_index IF NOT EXISTS FOR (c:Claim) ON (c.entailed_score)",
            "CREATE INDEX claim_coverage_score_index IF NOT EXISTS FOR (c:Claim) ON (c.coverage_score)",
            "CREATE INDEX claim_decontextualization_score_index IF NOT EXISTS FOR (c:Claim) ON (c.decontextualization_score)",
        ]
        
        with self.session() as session:
            for query in schema_queries:
                try:
                    session.run(query)
                    logger.debug(f"Executed schema query: {query}")
                except Exception as e:
                    logger.warning(f"Schema query failed (may already exist): {query}, error: {e}")
        
        logger.info("Neo4j schema setup completed")
    
    def create_claims(self, claim_inputs: List[ClaimInput]) -> List[Claim]:
        """
        Create Claim nodes in batch with ORIGINATES_FROM relationships.
        
        Args:
            claim_inputs: List of ClaimInput objects
            
        Returns:
            List of created Claim objects
        """
        if not claim_inputs:
            logger.warning("No claims provided for creation")
            return []
        
        # Convert inputs to Claim objects
        claims = [Claim.from_input(claim_input) for claim_input in claim_inputs]
        
        # Prepare data for batch creation
        claims_data = []
        for claim, claim_input in zip(claims, claim_inputs):
            claim_dict = claim.to_dict()
            claim_dict["block_id"] = claim_input.block_id
            claims_data.append(claim_dict)
        
        # Batch create using UNWIND (following architecture guidelines)
        cypher_query = """
        UNWIND $claims_data AS data
        MERGE (c:Claim {id: data.id})
        ON CREATE SET
            c.text = data.text,
            c.entailed_score = data.entailed_score,
            c.coverage_score = data.coverage_score,
            c.decontextualization_score = data.decontextualization_score,
            c.version = data.version,
            c.timestamp = datetime(data.timestamp)
        MERGE (b:Block {id: data.block_id})
        MERGE (c)-[:ORIGINATES_FROM]->(b)
        RETURN c.id as claim_id
        """
        
        try:
            with self.session() as session:
                result = session.run(cypher_query, claims_data=claims_data)
                created_ids = [record["claim_id"] for record in result]
                
            logger.info(f"Successfully created {len(created_ids)} Claim nodes")
            return claims
            
        except Exception as e:
            logger.error(f"Failed to create Claims: {e}")
            raise
    
    def create_sentences(self, sentence_inputs: List[SentenceInput]) -> List[Sentence]:
        """
        Create Sentence nodes in batch with ORIGINATES_FROM relationships.
        
        Args:
            sentence_inputs: List of SentenceInput objects
            
        Returns:
            List of created Sentence objects
        """
        if not sentence_inputs:
            logger.warning("No sentences provided for creation")
            return []
        
        # Convert inputs to Sentence objects
        sentences = [Sentence.from_input(sentence_input) for sentence_input in sentence_inputs]
        
        # Prepare data for batch creation
        sentences_data = []
        for sentence, sentence_input in zip(sentences, sentence_inputs):
            sentence_dict = sentence.to_dict()
            sentence_dict["block_id"] = sentence_input.block_id
            sentences_data.append(sentence_dict)
        
        # Batch create using UNWIND
        cypher_query = """
        UNWIND $sentences_data AS data
        MERGE (s:Sentence {id: data.id})
        ON CREATE SET
            s.text = data.text,
            s.ambiguous = data.ambiguous,
            s.verifiable = data.verifiable,
            s.version = data.version,
            s.timestamp = datetime(data.timestamp)
        MERGE (b:Block {id: data.block_id})
        MERGE (s)-[:ORIGINATES_FROM]->(b)
        RETURN s.id as sentence_id
        """
        
        try:
            with self.session() as session:
                result = session.run(cypher_query, sentences_data=sentences_data)
                created_ids = [record["sentence_id"] for record in result]
                
            logger.info(f"Successfully created {len(created_ids)} Sentence nodes")
            return sentences
            
        except Exception as e:
            logger.error(f"Failed to create Sentences: {e}")
            raise
    
    def get_claim_by_id(self, claim_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a Claim node by ID.
        
        Args:
            claim_id: The claim ID to search for
            
        Returns:
            Claim node data as dictionary, or None if not found
        """
        cypher_query = """
        MATCH (c:Claim {id: $claim_id})
        RETURN c.id as id, c.text as text, c.entailed_score as entailed_score,
               c.coverage_score as coverage_score, c.decontextualization_score as decontextualization_score,
               c.version as version, c.timestamp as timestamp
        """
        
        try:
            with self.session() as session:
                result = session.run(cypher_query, claim_id=claim_id)
                record = result.single()
                return dict(record) if record else None
                
        except Exception as e:
            logger.error(f"Failed to get Claim {claim_id}: {e}")
            raise
    
    def get_sentence_by_id(self, sentence_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a Sentence node by ID.
        
        Args:
            sentence_id: The sentence ID to search for
            
        Returns:
            Sentence node data as dictionary, or None if not found
        """
        cypher_query = """
        MATCH (s:Sentence {id: $sentence_id})
        RETURN s.id as id, s.text as text, s.ambiguous as ambiguous,
               s.verifiable as verifiable, s.version as version, s.timestamp as timestamp
        """
        
        try:
            with self.session() as session:
                result = session.run(cypher_query, sentence_id=sentence_id)
                record = result.single()
                return dict(record) if record else None
                
        except Exception as e:
            logger.error(f"Failed to get Sentence {sentence_id}: {e}")
            raise
    
    def count_nodes(self) -> Dict[str, int]:
        """
        Get count of nodes for monitoring/validation.
        
        Returns:
            Dictionary with node counts
        """
        cypher_query = """
        MATCH (c:Claim) WITH count(c) as claim_count
        MATCH (s:Sentence) WITH claim_count, count(s) as sentence_count
        MATCH (b:Block) WITH claim_count, sentence_count, count(b) as block_count
        RETURN claim_count, sentence_count, block_count
        """
        
        try:
            with self.session() as session:
                result = session.run(cypher_query)
                record = result.single()
                if record:
                    return {
                        "claims": record["claim_count"],
                        "sentences": record["sentence_count"], 
                        "blocks": record["block_count"]
                    }
                return {"claims": 0, "sentences": 0, "blocks": 0}
                
        except Exception as e:
            logger.error(f"Failed to count nodes: {e}")
            raise
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
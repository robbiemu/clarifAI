"""Tests for claim-concept linking models."""

from datetime import datetime

from aclarai_shared.claim_concept_linking.models import (
    AgentClassificationResult,
    ClaimConceptLinkResult,
    ClaimConceptPair,
    ConceptCandidate,
    LinkingError,
    RelationshipType,
)


class TestRelationshipType:
    """Test the RelationshipType enum."""

    def test_relationship_types(self):
        """Test that all expected relationship types exist."""
        assert RelationshipType.SUPPORTS_CONCEPT.value == "SUPPORTS_CONCEPT"
        assert RelationshipType.MENTIONS_CONCEPT.value == "MENTIONS_CONCEPT"
        assert RelationshipType.CONTRADICTS_CONCEPT.value == "CONTRADICTS_CONCEPT"


class TestClaimConceptPair:
    """Test the ClaimConceptPair data model."""

    def test_basic_pair_creation(self):
        """Test creating a basic claim-concept pair."""
        pair = ClaimConceptPair(
            claim_id="claim_123",
            claim_text="The system crashed due to memory overflow.",
            concept_id="concept_456",
            concept_text="memory error",
        )
        assert pair.claim_id == "claim_123"
        assert pair.claim_text == "The system crashed due to memory overflow."
        assert pair.concept_id == "concept_456"
        assert pair.concept_text == "memory error"
        assert pair.source_sentence is None
        assert pair.summary_block is None
        assert pair.entailed_score is None
        assert pair.coverage_score is None
        assert pair.decontextualization_score is None

    def test_pair_with_context(self):
        """Test creating a pair with contextual information."""
        pair = ClaimConceptPair(
            claim_id="claim_123",
            claim_text="The system crashed due to memory overflow.",
            concept_id="concept_456",
            concept_text="memory error",
            source_sentence="The application reported a fatal error and terminated.",
            summary_block="- System experienced memory-related failures",
            entailed_score=0.85,
            coverage_score=0.92,
            decontextualization_score=0.78,
        )
        assert (
            pair.source_sentence
            == "The application reported a fatal error and terminated."
        )
        assert pair.summary_block == "- System experienced memory-related failures"
        assert pair.entailed_score == 0.85
        assert pair.coverage_score == 0.92
        assert pair.decontextualization_score == 0.78

    def test_pair_with_null_scores(self):
        """Test pair with null scores (expected during Sprint 5)."""
        pair = ClaimConceptPair(
            claim_id="claim_123",
            claim_text="The system crashed.",
            concept_id="concept_456",
            concept_text="system error",
            entailed_score=None,
            coverage_score=None,
            decontextualization_score=None,
        )
        assert pair.entailed_score is None
        assert pair.coverage_score is None
        assert pair.decontextualization_score is None


class TestClaimConceptLinkResult:
    """Test the ClaimConceptLinkResult data model."""

    def test_basic_link_result(self):
        """Test creating a basic link result."""
        result = ClaimConceptLinkResult(
            claim_id="claim_123",
            concept_id="concept_456",
            relationship=RelationshipType.SUPPORTS_CONCEPT,
            strength=0.89,
        )
        assert result.claim_id == "claim_123"
        assert result.concept_id == "concept_456"
        assert result.relationship == RelationshipType.SUPPORTS_CONCEPT
        assert result.strength == 0.89
        assert result.entailed_score is None
        assert result.coverage_score is None
        assert result.classified_at is not None
        assert result.agent_model is None

    def test_link_result_with_scores(self):
        """Test link result with copied scores from claim."""
        result = ClaimConceptLinkResult(
            claim_id="claim_123",
            concept_id="concept_456",
            relationship=RelationshipType.MENTIONS_CONCEPT,
            strength=0.65,
            entailed_score=0.78,
            coverage_score=0.82,
            agent_model="gpt-4o",
        )
        assert result.entailed_score == 0.78
        assert result.coverage_score == 0.82
        assert result.agent_model == "gpt-4o"

    def test_link_result_with_null_scores(self):
        """Test link result with null scores (expected during Sprint 5)."""
        result = ClaimConceptLinkResult(
            claim_id="claim_123",
            concept_id="concept_456",
            relationship=RelationshipType.CONTRADICTS_CONCEPT,
            strength=0.92,
            entailed_score=None,
            coverage_score=None,
        )
        assert result.entailed_score is None
        assert result.coverage_score is None

    def test_to_neo4j_properties(self):
        """Test conversion to Neo4j properties."""
        timestamp = datetime(2024, 1, 15, 10, 30, 0)
        result = ClaimConceptLinkResult(
            claim_id="claim_123",
            concept_id="concept_456",
            relationship=RelationshipType.SUPPORTS_CONCEPT,
            strength=0.89,
            entailed_score=0.78,
            coverage_score=0.82,
            classified_at=timestamp,
            agent_model="gpt-4o",
        )
        properties = result.to_neo4j_properties()
        expected = {
            "strength": 0.89,
            "entailed_score": 0.78,
            "coverage_score": 0.82,
            "classified_at": "2024-01-15T10:30:00",
            "agent_model": "gpt-4o",
        }
        assert properties == expected

    def test_to_neo4j_properties_with_nulls(self):
        """Test Neo4j properties conversion with null values."""
        # Use a fixed timestamp to avoid auto-timestamping in __post_init__
        timestamp = datetime(2024, 1, 15, 10, 30, 0)
        result = ClaimConceptLinkResult(
            claim_id="claim_123",
            concept_id="concept_456",
            relationship=RelationshipType.MENTIONS_CONCEPT,
            strength=0.65,
            entailed_score=None,
            coverage_score=None,
            classified_at=timestamp,  # Use fixed timestamp
            agent_model=None,
        )
        # Manually set to None after creation to test null handling
        result.classified_at = None
        properties = result.to_neo4j_properties()
        assert properties["strength"] == 0.65
        assert properties["entailed_score"] is None
        assert properties["coverage_score"] is None
        assert properties["classified_at"] is None
        assert properties["agent_model"] is None


class TestLinkingError:
    """Test the LinkingError data model."""

    def test_basic_error(self):
        """Test creating a basic linking error."""
        error = LinkingError(
            claim_id="claim_123",
            concept_id="concept_456",
            error_type="classification_failed",
            error_message="LLM returned invalid JSON",
        )
        assert error.claim_id == "claim_123"
        assert error.concept_id == "concept_456"
        assert error.error_type == "classification_failed"
        assert error.error_message == "LLM returned invalid JSON"
        assert error.timestamp is not None

    def test_error_without_concept(self):
        """Test error where concept_id is not known."""
        error = LinkingError(
            claim_id="claim_123",
            error_type="no_candidates",
            error_message="No concept candidates found",
        )
        assert error.claim_id == "claim_123"
        assert error.concept_id is None
        assert error.error_type == "no_candidates"


class TestAgentClassificationResult:
    """Test the AgentClassificationResult data model."""

    def test_valid_classification(self):
        """Test creating a valid classification result."""
        result = AgentClassificationResult(
            relation="SUPPORTS_CONCEPT",
            strength=0.89,
            entailed_score=0.78,
            coverage_score=0.82,
        )
        assert result.relation == "SUPPORTS_CONCEPT"
        assert result.strength == 0.89
        assert result.entailed_score == 0.78
        assert result.coverage_score == 0.82

    def test_to_relationship_type_valid(self):
        """Test converting valid relation string to enum."""
        result = AgentClassificationResult(
            relation="MENTIONS_CONCEPT",
            strength=0.65,
        )
        relationship = result.to_relationship_type()
        assert relationship == RelationshipType.MENTIONS_CONCEPT

    def test_to_relationship_type_invalid(self):
        """Test converting invalid relation string."""
        result = AgentClassificationResult(
            relation="INVALID_RELATION",
            strength=0.50,
        )
        relationship = result.to_relationship_type()
        assert relationship is None

    def test_with_null_scores(self):
        """Test classification result with null scores."""
        result = AgentClassificationResult(
            relation="CONTRADICTS_CONCEPT",
            strength=0.92,
            entailed_score=None,
            coverage_score=None,
        )
        assert result.entailed_score is None
        assert result.coverage_score is None


class TestConceptCandidate:
    """Test the ConceptCandidate data model."""

    def test_basic_candidate(self):
        """Test creating a basic concept candidate."""
        candidate = ConceptCandidate(
            concept_id="concept_456",
            concept_text="memory error",
            similarity_score=0.85,
        )
        assert candidate.concept_id == "concept_456"
        assert candidate.concept_text == "memory error"
        assert candidate.similarity_score == 0.85
        assert candidate.source_node_id is None
        assert candidate.source_node_type is None
        assert candidate.aclarai_id is None

    def test_candidate_with_metadata(self):
        """Test candidate with source metadata."""
        candidate = ConceptCandidate(
            concept_id="concept_456",
            concept_text="memory error",
            similarity_score=0.85,
            source_node_id="claim_789",
            source_node_type="claim",
            aclarai_id="blk_abc123",
        )
        assert candidate.source_node_id == "claim_789"
        assert candidate.source_node_type == "claim"
        assert candidate.aclarai_id == "blk_abc123"

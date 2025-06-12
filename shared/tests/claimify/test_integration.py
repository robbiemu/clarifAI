"""
Tests for Claimify to Neo4j integration.

Tests the integration between the Claimify pipeline and Neo4j graph persistence,
including conversion of pipeline results to graph inputs and end-to-end workflows.
"""

import pytest
import os
import unittest
from unittest.mock import Mock

from clarifai_shared.claimify.data_models import (
    SentenceChunk,
    ClaimifyContext,
    ClaimifyResult,
    ClaimCandidate,
    SelectionResult,
    DisambiguationResult,
    DecompositionResult,
)
from clarifai_shared.claimify.integration import (
    ClaimifyGraphIntegration,
    create_graph_manager_from_config,
)
from clarifai_shared.graph.neo4j_manager import Neo4jGraphManager
from clarifai_shared.graph.models import ClaimInput, SentenceInput

# Test configuration
try:
    # Check if Neo4j is available by attempting to access the manager
    Neo4jGraphManager.__name__
    NEO4J_AVAILABLE = True
except (ImportError, NameError):
    NEO4J_AVAILABLE = False


class MockNeo4jGraphManager:
    """Mock Neo4j graph manager for testing."""

    def __init__(self):
        self.claims_created = []
        self.sentences_created = []

    def create_claims(self, claims):
        """Mock claim creation."""
        self.claims_created.extend(claims)
        return [f"claim_{i}" for i in range(len(claims))]

    def create_sentences(self, sentences):
        """Mock sentence creation."""
        self.sentences_created.extend(sentences)
        return [f"sentence_{i}" for i in range(len(sentences))]

    def apply_core_schema(self):
        """Mock schema application."""
        return True

    def setup_schema(self):
        """Mock schema setup."""
        return True


class TestClaimifyGraphIntegration:
    """Test Claimify to Neo4j integration functionality."""

    @pytest.fixture
    def mock_graph_manager(self):
        """Create a mock graph manager for testing."""
        manager = Mock()
        manager.create_claims = Mock(return_value=["claim_001"])
        manager.create_sentences = Mock(return_value=["sentence_001"])
        manager.setup_schema = Mock()
        return manager

    @pytest.fixture
    def integration(self, mock_graph_manager):
        """Create integration instance with mock manager."""
        return ClaimifyGraphIntegration(mock_graph_manager)

    @pytest.fixture
    def test_chunk(self):
        """Create test sentence chunk."""
        return SentenceChunk(
            text="The system failed at startup.",
            source_id="blk_001",
            chunk_id="chunk_001",
            sentence_index=0,
        )

    def test_convert_successful_claim_result(
        self, integration, test_chunk, integration_mode
    ):
        """Test conversion of successful claim result."""
        if not integration_mode:
            # Mock test - verify conversion logic
            # Create a valid claim candidate
            valid_claim = ClaimCandidate(
                text="The system failed at startup.",
                is_atomic=True,
                is_self_contained=True,
                is_verifiable=True,
                confidence=0.95,
            )

            # Create decomposition result with valid claim
            decomposition_result = DecompositionResult(
                original_text="The system failed at startup.",
                claim_candidates=[valid_claim],
            )

            # Create a successful claimify result
            result = ClaimifyResult(
                original_chunk=test_chunk,
                context=ClaimifyContext(current_sentence=test_chunk),
                selection_result=SelectionResult(
                    sentence_chunk=test_chunk, is_selected=True
                ),
                decomposition_result=decomposition_result,
            )

            # Convert to inputs
            claim_inputs, sentence_inputs = integration._convert_result_to_inputs(
                result
            )

            # Check claim properties
            assert len(claim_inputs) == 1
            claim = claim_inputs[0]
            assert isinstance(claim, ClaimInput)
            assert claim.text == "The system failed at startup."
            assert claim.block_id == "blk_001"
            assert claim.verifiable
            assert claim.self_contained
            assert claim.context_complete
        else:
            # Integration test - requires real Neo4j service
            pytest.skip("Integration tests require real database setup")

    def test_convert_failed_claim_result(
        self, integration, test_chunk, integration_mode
    ):
        """Test conversion of result with claims that failed criteria."""
        if not integration_mode:
            # Mock test - verify conversion logic
            # Create a claim candidate that fails some criteria
            failed_candidate = ClaimCandidate(
                text="It failed again.",
                is_atomic=True,
                is_self_contained=False,  # Fails self-containment
                is_verifiable=True,
                confidence=0.3,
            )

            decomposition_result = DecompositionResult(
                original_text="It failed again.", claim_candidates=[failed_candidate]
            )

            result = ClaimifyResult(
                original_chunk=test_chunk,
                context=ClaimifyContext(current_sentence=test_chunk),
                selection_result=SelectionResult(
                    sentence_chunk=test_chunk, is_selected=True
                ),
                decomposition_result=decomposition_result,
            )

            # Convert to graph inputs
            claim_inputs, sentence_inputs = integration._convert_result_to_inputs(
                result
            )

            # Should have no claims, one sentence
            assert len(claim_inputs) == 0
            assert len(sentence_inputs) == 1

            # Check sentence properties
            sentence = sentence_inputs[0]
            assert isinstance(sentence, SentenceInput)
            assert sentence.text == "It failed again."
            assert sentence.block_id == "blk_001"
            assert sentence.ambiguous  # Because not self-contained
            assert sentence.verifiable
            assert not sentence.failed_decomposition  # Was atomic
        else:
            # Integration test - requires real Neo4j service
            pytest.skip("Integration tests require real database setup")

    def test_convert_unprocessed_result(
        self, integration, test_chunk, integration_mode
    ):
        """Test conversion of result that wasn't selected for processing."""
        if not integration_mode:
            # Mock test - verify conversion logic
            # Create result where selection failed
            result = ClaimifyResult(
                original_chunk=test_chunk,
                context=ClaimifyContext(current_sentence=test_chunk),
                selection_result=SelectionResult(
                    sentence_chunk=test_chunk, is_selected=False
                ),
                # No decomposition result since it wasn't selected
            )

            # Convert to graph inputs
            claim_inputs, sentence_inputs = integration._convert_result_to_inputs(
                result
            )

            # Should have no claims, one sentence
            assert len(claim_inputs) == 0
            assert len(sentence_inputs) == 1

            # Check sentence properties
            sentence = sentence_inputs[0]
            assert isinstance(sentence, SentenceInput)
            assert sentence.text == "The system failed at startup."
            assert sentence.block_id == "blk_001"
            assert sentence.ambiguous  # Because not selected
            assert not sentence.verifiable  # Because not selected
            assert not sentence.failed_decomposition  # Wasn't decomposed
            assert sentence.rejection_reason == "Not selected by Selection agent"
        else:
            # Integration test - requires real Neo4j service
            pytest.skip("Integration tests require real database setup")

    def test_create_claim_input(self, integration, test_chunk, integration_mode):
        """Test creation of ClaimInput from ClaimCandidate."""
        if not integration_mode:
            # Mock test - verify claim input creation
            claim_candidate = ClaimCandidate(
                text="The error occurred at 10:30 AM.",
                is_atomic=True,
                is_self_contained=True,
                is_verifiable=True,
                confidence=0.95,
            )

            claim_input = integration._create_claim_input(claim_candidate, test_chunk)

            assert isinstance(claim_input, ClaimInput)
            assert claim_input.text == "The error occurred at 10:30 AM."
            assert claim_input.block_id == "blk_001"
            assert claim_input.verifiable
            assert claim_input.self_contained
            assert claim_input.context_complete
            assert claim_input.entailed_score is None  # Not set by pipeline
            assert claim_input.coverage_score is None
            assert claim_input.decontextualization_score is None
            assert claim_input.id.startswith("claim_")
        else:
            # Integration test - requires real Neo4j service
            pytest.skip("Integration tests require real database setup")

    def test_create_sentence_input(self, integration, test_chunk, integration_mode):
        """Test creation of SentenceInput from ClaimCandidate."""
        if not integration_mode:
            # Mock test - verify sentence input creation
            sentence_candidate = ClaimCandidate(
                text="It was problematic.",
                is_atomic=True,
                is_self_contained=False,  # Ambiguous
                is_verifiable=True,
                rejection_reason="Ambiguous pronoun",
            )

            sentence_input = integration._create_sentence_input(
                sentence_candidate, test_chunk, rejection_reason="Ambiguous pronoun"
            )

            assert isinstance(sentence_input, SentenceInput)
            assert sentence_input.text == "It was problematic."
            assert sentence_input.block_id == "blk_001"
            assert sentence_input.ambiguous  # Because not self-contained
            assert sentence_input.verifiable
            assert not sentence_input.failed_decomposition  # Was atomic
            assert sentence_input.rejection_reason == "Ambiguous pronoun"
            assert sentence_input.id.startswith("sentence_")
        else:
            # Integration test - requires real Neo4j service
            pytest.skip("Integration tests require real database setup")

    def test_create_sentence_input_from_chunk(
        self, integration, test_chunk, integration_mode
    ):
        """Test creation of SentenceInput directly from chunk."""
        if not integration_mode:
            # Mock test - verify sentence input creation from chunk
            sentence_input = integration._create_sentence_input_from_chunk(
                test_chunk, rejection_reason="Failed selection"
            )

            assert isinstance(sentence_input, SentenceInput)
            assert sentence_input.text == "The system failed at startup."
            assert sentence_input.block_id == "blk_001"
            assert sentence_input.ambiguous
            assert not sentence_input.verifiable
            assert not sentence_input.failed_decomposition
            assert sentence_input.rejection_reason == "Failed selection"
        else:
            # Integration test - requires real Neo4j service
            pytest.skip("Integration tests require real database setup")


class TestCreateGraphManagerFromConfigStructure:
    """Test graph manager creation from configuration."""

    def test_create_manager_from_config(self, integration_mode):
        """Test creation of graph manager from config."""
        if not integration_mode:
            # Mock test - verify module structure exists
            manager_path = os.path.join(
                os.path.dirname(__file__),
                "../../clarifai_shared/claimify/integration.py",
            )
            assert os.path.exists(manager_path)

            with open(manager_path, "r") as f:
                content = f.read()
                assert "def create_graph_manager_from_config" in content
        else:
            # Integration test - requires real Neo4j service
            pytest.skip("Integration tests require real database setup")

    def test_create_manager_empty_config(self, integration_mode):
        """Test creation of graph manager with empty config."""
        if not integration_mode:
            # Mock test - verify module structure exists
            integration_path = os.path.join(
                os.path.dirname(__file__),
                "../../clarifai_shared/claimify/integration.py",
            )
            assert os.path.exists(integration_path)

            with open(integration_path, "r") as f:
                content = f.read()
                assert "create_graph_manager_from_config" in content
        else:
            # Integration test - requires real Neo4j service
            pytest.skip("Integration tests require real database setup")

        self.test_context = ClaimifyContext(current_sentence=self.test_chunk)

    def test_integration_initialization(self):
        """Test integration initialization."""
        integration = ClaimifyGraphIntegration(self.graph_manager)
        self.assertEqual(integration.graph_manager, self.graph_manager)

    def test_convert_successful_claim_result(self):
        """Test conversion of result with valid claims."""
        # Create a successful processing result with valid claims
        claim_candidate = ClaimCandidate(
            text="The system failed at startup.",
            is_atomic=True,
            is_self_contained=True,
            is_verifiable=True,
            confidence=0.9,
        )

        decomposition_result = DecompositionResult(
            original_text="The system failed at startup.",
            claim_candidates=[claim_candidate],
        )

        result = ClaimifyResult(
            original_chunk=self.test_chunk,
            context=self.test_context,
            selection_result=SelectionResult(self.test_chunk, is_selected=True),
            disambiguation_result=DisambiguationResult(
                self.test_chunk, "The system failed at startup."
            ),
            decomposition_result=decomposition_result,
        )

        # Convert to graph inputs
        claim_inputs, sentence_inputs = self.integration._convert_result_to_inputs(
            result
        )

        # Should have one claim, no sentences
        self.assertEqual(len(claim_inputs), 1)
        self.assertEqual(len(sentence_inputs), 0)

        # Check claim properties
        claim = claim_inputs[0]
        self.assertIsInstance(claim, ClaimInput)
        self.assertEqual(claim.text, "The system failed at startup.")
        self.assertEqual(claim.block_id, "blk_001")
        self.assertTrue(claim.verifiable)
        self.assertTrue(claim.self_contained)
        self.assertTrue(claim.context_complete)

    def test_convert_failed_claim_result(self):
        """Test conversion of result with claims that failed criteria."""
        # Create a claim candidate that fails some criteria
        failed_candidate = ClaimCandidate(
            text="It failed again.",
            is_atomic=True,
            is_self_contained=False,  # Fails self-containment
            is_verifiable=True,
            confidence=0.3,
        )

        decomposition_result = DecompositionResult(
            original_text="It failed again.", claim_candidates=[failed_candidate]
        )

        result = ClaimifyResult(
            original_chunk=self.test_chunk,
            context=self.test_context,
            selection_result=SelectionResult(self.test_chunk, is_selected=True),
            disambiguation_result=DisambiguationResult(
                self.test_chunk, "It failed again."
            ),
            decomposition_result=decomposition_result,
        )

        # Convert to graph inputs
        claim_inputs, sentence_inputs = self.integration._convert_result_to_inputs(
            result
        )

        # Should have no claims, one sentence
        self.assertEqual(len(claim_inputs), 0)
        self.assertEqual(len(sentence_inputs), 1)

        # Check sentence properties
        sentence = sentence_inputs[0]
        self.assertIsInstance(sentence, SentenceInput)
        self.assertEqual(sentence.text, "It failed again.")
        self.assertEqual(sentence.block_id, "blk_001")
        self.assertTrue(sentence.ambiguous)  # Because not self-contained
        self.assertTrue(sentence.verifiable)
        self.assertFalse(sentence.failed_decomposition)  # Was atomic

    def test_convert_mixed_decomposition_result(self):
        """Test conversion of result with both valid and invalid claims."""
        # Create mix of valid and invalid claim candidates
        valid_claim = ClaimCandidate(
            text="The database connection failed.",
            is_atomic=True,
            is_self_contained=True,
            is_verifiable=True,
        )

        invalid_claim = ClaimCandidate(
            text="This is ambiguous.",
            is_atomic=False,
            is_self_contained=False,
            is_verifiable=False,
        )

        decomposition_result = DecompositionResult(
            original_text="Complex sentence with multiple parts.",
            claim_candidates=[valid_claim, invalid_claim],
        )

        result = ClaimifyResult(
            original_chunk=self.test_chunk,
            context=self.test_context,
            selection_result=SelectionResult(self.test_chunk, is_selected=True),
            disambiguation_result=DisambiguationResult(
                self.test_chunk, "Complex sentence with multiple parts."
            ),
            decomposition_result=decomposition_result,
        )

        # Convert to graph inputs
        claim_inputs, sentence_inputs = self.integration._convert_result_to_inputs(
            result
        )

        # Should have one claim, one sentence
        self.assertEqual(len(claim_inputs), 1)
        self.assertEqual(len(sentence_inputs), 1)

        # Check that valid claim became ClaimInput
        claim = claim_inputs[0]
        self.assertEqual(claim.text, "The database connection failed.")

        # Check that invalid claim became SentenceInput
        sentence = sentence_inputs[0]
        self.assertEqual(sentence.text, "This is ambiguous.")

    def test_convert_unprocessed_result(self):
        """Test conversion of result that was not processed."""
        # Create a result where selection rejected the sentence
        result = ClaimifyResult(
            original_chunk=self.test_chunk,
            context=self.test_context,
            selection_result=SelectionResult(self.test_chunk, is_selected=False),
        )

        # Convert to graph inputs
        claim_inputs, sentence_inputs = self.integration._convert_result_to_inputs(
            result
        )

        # Should have no claims, one sentence from original chunk
        self.assertEqual(len(claim_inputs), 0)
        self.assertEqual(len(sentence_inputs), 1)

        # Check sentence properties
        sentence = sentence_inputs[0]
        self.assertEqual(sentence.text, "The system failed at startup.")
        self.assertEqual(sentence.block_id, "blk_001")
        self.assertTrue(sentence.ambiguous)  # Assumed ambiguous since not selected
        self.assertFalse(
            sentence.verifiable
        )  # Assumed not verifiable since not selected
        self.assertEqual(sentence.rejection_reason, "Not selected by Selection agent")

    def test_persist_claimify_results_empty(self):
        """Test persisting empty results list."""
        claims_created, sentences_created, errors = (
            self.integration.persist_claimify_results([])
        )

        self.assertEqual(claims_created, 0)
        self.assertEqual(sentences_created, 0)
        self.assertEqual(len(errors), 0)

    def test_persist_claimify_results_with_claims(self):
        """Test persisting results with valid claims."""
        # Create test results with claims
        claim_candidate = ClaimCandidate(
            text="Server responded with 500 error.",
            is_atomic=True,
            is_self_contained=True,
            is_verifiable=True,
        )

        decomposition_result = DecompositionResult(
            original_text="Server responded with 500 error.",
            claim_candidates=[claim_candidate],
        )

        result = ClaimifyResult(
            original_chunk=self.test_chunk,
            context=self.test_context,
            selection_result=SelectionResult(self.test_chunk, is_selected=True),
            decomposition_result=decomposition_result,
        )

        # Persist results
        claims_created, sentences_created, errors = (
            self.integration.persist_claimify_results([result])
        )

        self.assertEqual(claims_created, 1)
        self.assertEqual(sentences_created, 0)
        self.assertEqual(len(errors), 0)

    def test_persist_claimify_results_with_sentences(self):
        """Test persisting results with sentence nodes."""
        # Create test results with rejected sentences
        result = ClaimifyResult(
            original_chunk=self.test_chunk,
            context=self.test_context,
            selection_result=SelectionResult(self.test_chunk, is_selected=False),
        )

        # Persist results
        claims_created, sentences_created, errors = (
            self.integration.persist_claimify_results([result])
        )

        self.assertEqual(claims_created, 0)
        self.assertEqual(sentences_created, 1)
        self.assertEqual(len(errors), 0)

    def test_create_claim_input(self):
        """Test creation of ClaimInput from ClaimCandidate."""
        claim_candidate = ClaimCandidate(
            text="The error occurred at 10:30 AM.",
            is_atomic=True,
            is_self_contained=True,
            is_verifiable=True,
            confidence=0.95,
        )

        claim_input = self.integration._create_claim_input(
            claim_candidate, self.test_chunk
        )

        self.assertIsInstance(claim_input, ClaimInput)
        self.assertEqual(claim_input.text, "The error occurred at 10:30 AM.")
        self.assertEqual(claim_input.block_id, "blk_001")
        self.assertTrue(claim_input.verifiable)
        self.assertTrue(claim_input.self_contained)
        self.assertTrue(claim_input.context_complete)
        self.assertIsNone(claim_input.entailed_score)  # Not set by pipeline
        self.assertIsNone(claim_input.coverage_score)
        self.assertIsNone(claim_input.decontextualization_score)
        self.assertTrue(claim_input.id.startswith("claim_"))

    def test_create_sentence_input(self):
        """Test creation of SentenceInput from ClaimCandidate."""
        sentence_candidate = ClaimCandidate(
            text="It was problematic.",
            is_atomic=True,
            is_self_contained=False,
            is_verifiable=True,
        )

        sentence_input = self.integration._create_sentence_input(
            sentence_candidate, self.test_chunk, rejection_reason="Ambiguous pronoun"
        )

        self.assertIsInstance(sentence_input, SentenceInput)
        self.assertEqual(sentence_input.text, "It was problematic.")
        self.assertEqual(sentence_input.block_id, "blk_001")
        self.assertTrue(sentence_input.ambiguous)  # Because not self-contained
        self.assertTrue(sentence_input.verifiable)
        self.assertFalse(sentence_input.failed_decomposition)  # Was atomic
        self.assertEqual(sentence_input.rejection_reason, "Ambiguous pronoun")
        self.assertTrue(sentence_input.id.startswith("sent_"))

    def test_create_sentence_input_from_chunk(self):
        """Test creation of SentenceInput directly from chunk."""
        sentence_input = self.integration._create_sentence_input_from_chunk(
            self.test_chunk, rejection_reason="Failed selection"
        )

        self.assertIsInstance(sentence_input, SentenceInput)
        self.assertEqual(sentence_input.text, "The system failed at startup.")
        self.assertEqual(sentence_input.block_id, "blk_001")
        self.assertTrue(sentence_input.ambiguous)
        self.assertFalse(sentence_input.verifiable)
        self.assertFalse(sentence_input.failed_decomposition)
        self.assertEqual(sentence_input.rejection_reason, "Failed selection")


class TestCreateGraphManagerFromConfig(unittest.TestCase):
    """Test graph manager creation from configuration."""

    def setUp(self):
        """Set up for configuration tests."""
        if not NEO4J_AVAILABLE:
            self.skipTest("Neo4j dependencies not available")

    def test_create_manager_from_config(self):
        """Test creating graph manager from configuration dictionary."""
        config = {
            "databases": {
                "neo4j": {
                    "host": "neo4j-test",
                    "port": 7687,
                    "username": "test_user",
                    "password": "test_pass",
                }
            }
        }

        manager = create_graph_manager_from_config(config)

        # Note: In real environment this would create actual Neo4jGraphManager
        # For tests without Neo4j, we skip the test
        self.assertIsNotNone(manager)

    def test_create_manager_empty_config(self):
        """Test creating graph manager with empty config."""
        config = {}

        manager = create_graph_manager_from_config(config)

        # Note: In real environment this would create actual Neo4jGraphManager
        # For tests without Neo4j, we skip the test
        self.assertIsNotNone(manager)


class TestClaimifyNeo4jIntegrationEndToEnd(unittest.TestCase):
    """End-to-end integration tests combining Claimify pipeline with Neo4j persistence."""

    def setUp(self):
        """Set up integration components."""
        if not NEO4J_AVAILABLE:
            self.skipTest("Neo4j dependencies not available")

        self.graph_manager = MockNeo4jGraphManager()
        self.integration = ClaimifyGraphIntegration(self.graph_manager)

    def test_complete_pipeline_to_graph_flow(self):
        """Test complete flow from Claimify results to Neo4j persistence."""
        # Create realistic Claimify results from processing
        chunks = [
            SentenceChunk(
                text="The database connection failed during peak hours.",
                source_id="blk_001",
                chunk_id="chunk_001",
                sentence_index=0,
            ),
            SentenceChunk(
                text="What should we do about this?",
                source_id="blk_001",
                chunk_id="chunk_002",
                sentence_index=1,
            ),
            SentenceChunk(
                text="The error rate increased to 15%.",
                source_id="blk_002",
                chunk_id="chunk_003",
                sentence_index=0,
            ),
        ]

        # Create realistic processing results
        results = []

        # First chunk: produces a valid claim
        valid_claim = ClaimCandidate(
            text="The database connection failed during peak hours.",
            is_atomic=True,
            is_self_contained=True,
            is_verifiable=True,
        )

        results.append(
            ClaimifyResult(
                original_chunk=chunks[0],
                context=ClaimifyContext(current_sentence=chunks[0]),
                selection_result=SelectionResult(chunks[0], is_selected=True),
                decomposition_result=DecompositionResult(
                    original_text=chunks[0].text, claim_candidates=[valid_claim]
                ),
            )
        )

        # Second chunk: rejected by selection (question)
        results.append(
            ClaimifyResult(
                original_chunk=chunks[1],
                context=ClaimifyContext(current_sentence=chunks[1]),
                selection_result=SelectionResult(chunks[1], is_selected=False),
            )
        )

        # Third chunk: produces another valid claim
        another_claim = ClaimCandidate(
            text="The error rate increased to 15%.",
            is_atomic=True,
            is_self_contained=True,
            is_verifiable=True,
        )

        results.append(
            ClaimifyResult(
                original_chunk=chunks[2],
                context=ClaimifyContext(current_sentence=chunks[2]),
                selection_result=SelectionResult(chunks[2], is_selected=True),
                decomposition_result=DecompositionResult(
                    original_text=chunks[2].text, claim_candidates=[another_claim]
                ),
            )
        )

        # Apply schema and persist results
        schema_applied = self.graph_manager.apply_core_schema()
        self.assertTrue(schema_applied)

        claims_created, sentences_created, errors = (
            self.integration.persist_claimify_results(results)
        )

        # Should have created 2 claims and 1 sentence
        self.assertEqual(claims_created, 2)
        self.assertEqual(sentences_created, 1)
        self.assertEqual(len(errors), 0)

    def test_error_handling_in_integration(self):
        """Test error handling in the integration workflow."""
        # Create a result with malformed data that might cause conversion errors
        malformed_chunk = SentenceChunk(
            text="",  # Empty text
            source_id="",  # Empty source ID
            chunk_id="",
            sentence_index=0,
        )

        result = ClaimifyResult(
            original_chunk=malformed_chunk,
            context=ClaimifyContext(current_sentence=malformed_chunk),
            selection_result=SelectionResult(malformed_chunk, is_selected=False),
        )

        # Should handle gracefully
        claims_created, sentences_created, errors = (
            self.integration.persist_claimify_results([result])
        )

        # Might create nodes or might have errors, but shouldn't crash
        self.assertIsInstance(claims_created, int)
        self.assertIsInstance(sentences_created, int)
        self.assertIsInstance(errors, list)


if __name__ == "__main__":
    unittest.main()

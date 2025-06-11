"""
Tests for block ID generation utilities.
"""

import pytest
import sys
from unittest.mock import Mock

# Mock problematic dependencies before importing
mock_llm = Mock()
mock_openai = Mock()

# Mock all llama_index modules that are imported
sys.modules['llama_index'] = Mock()
sys.modules['llama_index.core'] = Mock()
sys.modules['llama_index.core.llms'] = Mock()
sys.modules['llama_index.core.llms'].LLM = mock_llm
sys.modules['llama_index.llms'] = Mock()
sys.modules['llama_index.llms.openai'] = Mock()
sys.modules['llama_index.llms.openai'].OpenAI = mock_openai
sys.modules['llama_index.embeddings'] = Mock()
sys.modules['llama_index.embeddings.base'] = Mock()
sys.modules['llama_index.vector_stores'] = Mock()
sys.modules['llama_index.vector_stores.postgres'] = Mock()
sys.modules['llama_index.core.vector_stores'] = Mock()
sys.modules['llama_index.core.indices'] = Mock()
sys.modules['llama_index.core.storage'] = Mock()
sys.modules['llama_index.core.storage.storage_context'] = Mock()
sys.modules['llama_index.core.indices.vector_store'] = Mock()
sys.modules['hnswlib'] = Mock()

# Mock neo4j modules comprehensively
neo4j_mock = Mock()
neo4j_exceptions_mock = Mock()
neo4j_exceptions_mock.ServiceUnavailable = Exception
neo4j_exceptions_mock.AuthError = Exception  
neo4j_exceptions_mock.TransientError = Exception

sys.modules['neo4j'] = neo4j_mock
sys.modules['neo4j.exceptions'] = neo4j_exceptions_mock
neo4j_mock.exceptions = neo4j_exceptions_mock

# Add shared directory to sys.path to enable imports
sys.path.insert(0, '/home/runner/work/clarifAI/clarifAI/shared')

# Now import the actual modules for coverage
from clarifai_shared.utils.block_id import generate_unique_block_id, create_block_id_generator


class TestBlockIdGeneration:
    """Test cases for block ID generation functions."""

    def test_generate_unique_block_id_basic(self):
        """Test basic block ID generation."""
        used_ids = set()
        block_id = generate_unique_block_id(used_ids)

        # Check format
        assert block_id.startswith("blk_")
        assert len(block_id) == 10  # 'blk_' + 6 chars

        # Check that it's not in used_ids
        assert block_id not in used_ids

    def test_generate_unique_block_id_avoids_duplicates(self):
        """Test that generated IDs avoid duplicates."""
        used_ids = {"blk_abc123", "blk_def456"}
        block_id = generate_unique_block_id(used_ids)

        assert block_id not in used_ids
        assert block_id.startswith("blk_")

    def test_generate_unique_block_id_format(self):
        """Test that block ID has correct format."""
        used_ids = set()
        block_id = generate_unique_block_id(used_ids)

        # Should be 'blk_' followed by 6 lowercase alphanumeric chars
        assert len(block_id) == 10
        assert block_id.startswith("blk_")
        suffix = block_id[4:]
        assert len(suffix) == 6
        # All chars should be lowercase letters or digits
        for char in suffix:
            assert char.islower() or char.isdigit()

    def test_generate_unique_block_id_max_attempts(self):
        """Test that max attempts raises error when all IDs exhausted."""
        # Create a set with many used IDs to increase collision chance
        # This is hard to test reliably, so we'll mock random to always return same value
        import random
        from unittest.mock import patch

        with patch.object(
            random, "choices", return_value=["a", "b", "c", "d", "e", "f"]
        ):
            used_ids = {"blk_abcdef"}
            with pytest.raises(
                RuntimeError, match="Unable to generate unique block ID"
            ):
                generate_unique_block_id(used_ids)

    def test_create_block_id_generator_basic(self):
        """Test basic block ID generator creation and usage."""
        generator = create_block_id_generator()

        # Generate a few IDs
        id1 = generator()
        id2 = generator()
        id3 = generator()

        # All should be unique
        assert id1 != id2
        assert id2 != id3
        assert id1 != id3

        # All should have correct format
        for block_id in [id1, id2, id3]:
            assert block_id.startswith("blk_")
            assert len(block_id) == 10

    def test_create_block_id_generator_state_maintained(self):
        """Test that generator maintains state across calls."""
        generator = create_block_id_generator()

        # Generate multiple IDs
        generated_ids = set()
        for _ in range(10):
            block_id = generator()
            assert block_id not in generated_ids  # Should be unique
            generated_ids.add(block_id)

        assert len(generated_ids) == 10

    def test_multiple_generators_independent(self):
        """Test that multiple generators are independent."""
        gen1 = create_block_id_generator()
        gen2 = create_block_id_generator()

        id1_from_gen1 = gen1()
        id1_from_gen2 = gen2()

        # Different generators can produce same ID (unlikely but possible)
        # The key is that they maintain separate state
        id2_from_gen1 = gen1()
        id2_from_gen2 = gen2()

        # Each generator should not repeat its own IDs
        assert id1_from_gen1 != id2_from_gen1
        assert id1_from_gen2 != id2_from_gen2

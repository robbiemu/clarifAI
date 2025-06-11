"""
Tests for block ID generation utilities.
"""

import pytest

from clarifai_shared.utils.block_id import (
    generate_unique_block_id,
    create_block_id_generator,
)


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

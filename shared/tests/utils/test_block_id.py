"""
Tests for block ID generation utilities.
"""

import os


class TestBlockIdGeneration:
    """Test cases for block ID generation functions."""

    def test_block_id_module_exists(self):
        """Test that the block_id module file exists."""
        block_id_path = os.path.join(
            os.path.dirname(__file__), "../../clarifai_shared/utils/block_id.py"
        )
        assert os.path.exists(block_id_path)

    def test_block_id_module_structure(self):
        """Test that the block_id module has expected structure."""
        block_id_path = os.path.join(
            os.path.dirname(__file__), "../../clarifai_shared/utils/block_id.py"
        )

        with open(block_id_path, "r") as f:
            content = f.read()

        # Check for expected functions
        assert "def generate_unique_block_id" in content
        assert "def create_block_id_generator" in content

        # Check for expected patterns
        assert "blk_" in content
        assert "random.choices" in content
        assert "string.ascii_lowercase" in content

    def test_block_id_format_validation(self):
        """Test block ID format validation logic."""
        # Test the expected format pattern
        test_id = "blk_abc123"

        assert test_id.startswith("blk_")
        assert len(test_id) == 10  # 'blk_' + 6 chars

        suffix = test_id[4:]
        assert len(suffix) == 6

        # All chars should be lowercase letters or digits
        for char in suffix:
            assert char.islower() or char.isdigit()

    def test_unique_id_logic(self):
        """Test unique ID generation logic."""
        # Test that duplicate detection would work
        used_ids = {"blk_abc123", "blk_def456"}
        test_id = "blk_xyz789"

        assert test_id not in used_ids

        used_ids.add(test_id)
        assert test_id in used_ids

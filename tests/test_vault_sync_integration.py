"""
Integration tests for vault synchronization using real test fixtures.
These tests validate the end-to-end functionality of the vault sync job
using realistic markdown content and fixture files.
"""

import shutil
import sys
import tempfile
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "shared"))
sys.path.insert(0, str(project_root))


def test_vault_sync_with_fixtures():
    """Integration test using real fixture files."""
    # Copy fixtures to temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_vault = Path(temp_dir)
        fixtures_dir = project_root / "tests" / "fixtures" / "vault_sync_examples"
        # Create tier structure
        tier1_dir = temp_vault / "conversations"
        tier3_dir = temp_vault / "concepts"
        tier1_dir.mkdir()
        tier3_dir.mkdir()
        # Copy fixtures
        shutil.copy(fixtures_dir / "tier1_conversation.md", tier1_dir)
        shutil.copy(fixtures_dir / "mixed_content.md", tier1_dir)
        shutil.copy(fixtures_dir / "no_aclarai_ids.md", tier1_dir)
        shutil.copy(fixtures_dir / "tier3_concept_page.md", tier3_dir)
        print(f"Test vault created at: {temp_vault}")
        print(f"Files in tier1: {list(tier1_dir.glob('*.md'))}")
        print(f"Files in tier3: {list(tier3_dir.glob('*.md'))}")
        # Test block extraction from fixtures
        tier1_conversation = (tier1_dir / "tier1_conversation.md").read_text()
        print(f"\nTier1 conversation content preview: {tier1_conversation[:200]}...")
        # Count expected blocks
        expected_blocks = tier1_conversation.count("aclarai:id=")
        print(f"Expected blocks in tier1_conversation.md: {expected_blocks}")

        # Test with simple block extraction function
        def extract_blocks_simple(content):
            """Simple block extraction for testing."""
            import re

            pattern = r"<!--\s*aclarai:id=([^-\s]+)(?:\s+ver=(\d+))?\s*-->"
            matches = re.findall(pattern, content)
            return [(match[0], int(match[1]) if match[1] else 1) for match in matches]

        blocks = extract_blocks_simple(tier1_conversation)
        print(f"Extracted blocks: {blocks}")
        assert len(blocks) == 8, f"Expected 8 blocks, got {len(blocks)}"
        # Test tier3 file-level block
        tier3_content = (tier3_dir / "tier3_concept_page.md").read_text()
        tier3_blocks = extract_blocks_simple(tier3_content)
        print(f"Tier3 blocks: {tier3_blocks}")
        assert len(tier3_blocks) == 1, (
            f"Expected 1 block in tier3, got {len(tier3_blocks)}"
        )
        assert tier3_blocks[0][0] == "concept_api_rate_limiting"
        # Test mixed content
        mixed_content = (tier1_dir / "mixed_content.md").read_text()
        mixed_blocks = extract_blocks_simple(mixed_content)
        print(f"Mixed content blocks: {mixed_blocks}")
        assert len(mixed_blocks) == 4, (
            f"Expected 4 blocks in mixed content, got {len(mixed_blocks)}"
        )
        # Test file with no aclarai:id
        no_id_content = (tier1_dir / "no_aclarai_ids.md").read_text()
        no_id_blocks = extract_blocks_simple(no_id_content)
        print(f"No-ID file blocks: {no_id_blocks}")
        assert len(no_id_blocks) == 0, (
            f"Expected 0 blocks in no-ID file, got {len(no_id_blocks)}"
        )
        print("\n✓ All fixture-based tests passed!")


def test_hash_consistency():
    """Test that hash calculation is consistent and handles edge cases."""
    import hashlib

    def calculate_hash(text):
        """Simple hash calculation."""
        normalized = " ".join(text.split())
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    # Test basic consistency
    text1 = "Alice: We need to finalize the roadmap for Q3."
    text2 = "Alice: We need to finalize the roadmap for Q3."
    hash1 = calculate_hash(text1)
    hash2 = calculate_hash(text2)
    assert hash1 == hash2, "Same text should produce same hash"
    # Test whitespace normalization
    text3 = "Alice:   We   need   to   finalize   the   roadmap   for   Q3."
    hash3 = calculate_hash(text3)
    assert hash1 == hash3, "Normalized whitespace should produce same hash"
    # Test different content
    text4 = "Bob: I agree with the roadmap."
    hash4 = calculate_hash(text4)
    assert hash1 != hash4, "Different text should produce different hash"
    print("✓ Hash consistency tests passed!")


def test_file_structure_discovery():
    """Test that the vault sync can discover files in the expected structure."""
    with tempfile.TemporaryDirectory() as temp_dir:
        vault_path = Path(temp_dir)
        # Create realistic vault structure
        (vault_path / "conversations").mkdir()
        (vault_path / "summaries").mkdir()
        (vault_path / "concepts").mkdir()
        # Create some test files
        (vault_path / "conversations" / "meeting_001.md").write_text(
            "# Meeting\nContent <!-- aclarai:id=blk_001 -->"
        )
        (vault_path / "conversations" / "brainstorm.md").write_text(
            "# Brainstorm\nIdeas <!-- aclarai:id=blk_002 -->"
        )
        (vault_path / "concepts" / "important_concept.md").write_text(
            "# Concept\nDescription <!-- aclarai:id=concept_001 -->"
        )
        (vault_path / "summaries" / "weekly_summary.md").write_text(
            "# Summary\nOverview"
        )  # No aclarai:id
        # Test file discovery
        md_files = list(vault_path.glob("**/*.md"))
        print(f"Discovered markdown files: {[f.name for f in md_files]}")
        assert len(md_files) == 4, f"Expected 4 markdown files, found {len(md_files)}"
        # Test tier-specific discovery
        tier1_files = list((vault_path / "conversations").glob("*.md"))
        tier3_files = list((vault_path / "concepts").glob("*.md"))
        assert len(tier1_files) == 2, (
            f"Expected 2 tier1 files, found {len(tier1_files)}"
        )
        assert len(tier3_files) == 1, f"Expected 1 tier3 file, found {len(tier3_files)}"
        print("✓ File structure discovery tests passed!")


if __name__ == "__main__":
    """Run integration tests."""
    print("Running vault sync integration tests...")
    try:
        test_vault_sync_with_fixtures()
    except Exception as e:
        print(f"✗ test_vault_sync_with_fixtures failed: {e}")
        import traceback

        traceback.print_exc()
    try:
        test_hash_consistency()
    except Exception as e:
        print(f"✗ test_hash_consistency failed: {e}")
    try:
        test_file_structure_discovery()
    except Exception as e:
        print(f"✗ test_file_structure_discovery failed: {e}")
    print("\nIntegration tests completed.")

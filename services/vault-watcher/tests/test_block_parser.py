"""
Tests for the vault watcher block parser functionality.
"""

import pytest
from pathlib import Path
import tempfile
import textwrap
from clarifai_vault_watcher.block_parser import BlockParser, ClarifAIBlock


class TestBlockParser:
    """Test cases for the BlockParser class."""
    
    def setup_method(self):
        """Set up test instances."""
        self.parser = BlockParser()
    
    def test_parse_inline_block(self):
        """Test parsing of inline blocks."""
        content = textwrap.dedent("""
        This is a regular paragraph.
        
        This is a claim about something important. <!-- clarifai:id=clm_test123 ver=1 -->
        ^clm_test123
        
        Another paragraph here.
        """).strip()
        
        blocks = self.parser.parse_content(content)
        
        assert len(blocks) == 1
        block = blocks[0]
        assert block.clarifai_id == "clm_test123"
        assert block.version == 1
        assert block.block_type == "inline"
        assert "This is a claim about something important." in block.content
    
    def test_parse_file_level_block(self):
        """Test parsing of file-level blocks."""
        content = textwrap.dedent("""
        # Top Concepts
        
        This is the content of the entire file.
        
        - Concept A
        - Concept B
        
        <!-- clarifai:id=file_concepts_20240522 ver=2 -->
        """).strip()
        
        blocks = self.parser.parse_content(content)
        
        assert len(blocks) == 1
        block = blocks[0]
        assert block.clarifai_id == "file_concepts_20240522"
        assert block.version == 2
        assert block.block_type == "file"
        assert "# Top Concepts" in block.content
        assert "<!-- clarifai:id" not in block.content  # Comment excluded from content
    
    def test_parse_mixed_blocks(self):
        """Test parsing a file with both inline and file-level blocks."""
        content = textwrap.dedent("""
        # Document Title
        
        This is an inline claim. <!-- clarifai:id=clm_inline1 ver=1 -->
        ^clm_inline1
        
        Another claim here. <!-- clarifai:id=clm_inline2 ver=3 -->
        ^clm_inline2
        
        Final paragraph.
        
        <!-- clarifai:id=file_doc123 ver=1 -->
        """).strip()
        
        blocks = self.parser.parse_content(content)
        
        # Should have 3 blocks: 2 inline + 1 file-level
        assert len(blocks) == 3
        
        # Find each block type
        file_blocks = [b for b in blocks if b.block_type == "file"]
        inline_blocks = [b for b in blocks if b.block_type == "inline"]
        
        assert len(file_blocks) == 1
        assert len(inline_blocks) == 2
        
        assert file_blocks[0].clarifai_id == "file_doc123"
        assert "clm_inline1" in [b.clarifai_id for b in inline_blocks]
        assert "clm_inline2" in [b.clarifai_id for b in inline_blocks]
    
    def test_parse_no_blocks(self):
        """Test parsing content with no ClarifAI blocks."""
        content = textwrap.dedent("""
        # Regular Document
        
        This is just a normal document.
        No special markers here.
        
        Just regular Markdown content.
        """).strip()
        
        blocks = self.parser.parse_content(content)
        assert len(blocks) == 0
    
    def test_parse_file_from_disk(self):
        """Test parsing a file from disk."""
        content = textwrap.dedent("""
        Test file content.
        
        This is a test claim. <!-- clarifai:id=clm_filetest ver=1 -->
        ^clm_filetest
        """).strip()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(content)
            temp_path = Path(f.name)
        
        try:
            blocks = self.parser.parse_file(temp_path)
            assert len(blocks) == 1
            assert blocks[0].clarifai_id == "clm_filetest"
        finally:
            temp_path.unlink()
    
    def test_parse_file_not_found(self):
        """Test handling of non-existent files."""
        with pytest.raises(FileNotFoundError):
            self.parser.parse_file(Path("/nonexistent/file.md"))
    
    def test_content_hash_consistency(self):
        """Test that content hashes are consistent."""
        content1 = "This is a test claim."
        content2 = "This is a test claim."  # Identical content
        content3 = "This is a different claim."  # Different content
        
        hash1 = self.parser._compute_content_hash(content1)
        hash2 = self.parser._compute_content_hash(content2)
        hash3 = self.parser._compute_content_hash(content3)
        
        assert hash1 == hash2
        assert hash1 != hash3
        assert len(hash1) == 64  # SHA-256 hex length
    
    def test_content_hash_whitespace_normalization(self):
        """Test that whitespace is normalized in content hashing."""
        content1 = "This is a test claim."
        content2 = "This  is   a    test     claim."  # Extra spaces
        content3 = "\n\tThis is a test claim.\n\n"  # Different whitespace
        
        hash1 = self.parser._compute_content_hash(content1)
        hash2 = self.parser._compute_content_hash(content2)
        hash3 = self.parser._compute_content_hash(content3)
        
        # All should be the same after normalization
        assert hash1 == hash2 == hash3
    
    def test_compare_blocks_no_changes(self):
        """Test block comparison with no changes."""
        block1 = ClarifAIBlock(
            clarifai_id="clm_test1",
            version=1,
            content="Test content",
            content_hash="abc123",
            start_pos=0,
            end_pos=10,
            block_type="inline"
        )
        
        old_blocks = [block1]
        new_blocks = [block1]  # Same block
        
        diff = self.parser.compare_blocks(old_blocks, new_blocks)
        
        assert len(diff['added']) == 0
        assert len(diff['modified']) == 0
        assert len(diff['deleted']) == 0
    
    def test_compare_blocks_added(self):
        """Test block comparison with added blocks."""
        block1 = ClarifAIBlock(
            clarifai_id="clm_existing",
            version=1,
            content="Existing content",
            content_hash="abc123",
            start_pos=0,
            end_pos=10,
            block_type="inline"
        )
        
        block2 = ClarifAIBlock(
            clarifai_id="clm_new",
            version=1,
            content="New content",
            content_hash="def456",
            start_pos=20,
            end_pos=30,
            block_type="inline"
        )
        
        old_blocks = [block1]
        new_blocks = [block1, block2]
        
        diff = self.parser.compare_blocks(old_blocks, new_blocks)
        
        assert len(diff['added']) == 1
        assert len(diff['modified']) == 0
        assert len(diff['deleted']) == 0
        assert diff['added'][0]['clarifai_id'] == "clm_new"
    
    def test_compare_blocks_modified(self):
        """Test block comparison with modified blocks."""
        block1_old = ClarifAIBlock(
            clarifai_id="clm_test",
            version=1,
            content="Old content",
            content_hash="abc123",
            start_pos=0,
            end_pos=10,
            block_type="inline"
        )
        
        block1_new = ClarifAIBlock(
            clarifai_id="clm_test",
            version=2,
            content="New content",
            content_hash="def456",
            start_pos=0,
            end_pos=10,
            block_type="inline"
        )
        
        old_blocks = [block1_old]
        new_blocks = [block1_new]
        
        diff = self.parser.compare_blocks(old_blocks, new_blocks)
        
        assert len(diff['added']) == 0
        assert len(diff['modified']) == 1
        assert len(diff['deleted']) == 0
        
        modified = diff['modified'][0]
        assert modified['clarifai_id'] == "clm_test"
        assert modified['old_version'] == 1
        assert modified['new_version'] == 2
        assert modified['old_hash'] == "abc123"
        assert modified['new_hash'] == "def456"
    
    def test_compare_blocks_deleted(self):
        """Test block comparison with deleted blocks."""
        block1 = ClarifAIBlock(
            clarifai_id="clm_deleted",
            version=1,
            content="Content to be deleted",
            content_hash="abc123",
            start_pos=0,
            end_pos=10,
            block_type="inline"
        )
        
        old_blocks = [block1]
        new_blocks = []
        
        diff = self.parser.compare_blocks(old_blocks, new_blocks)
        
        assert len(diff['added']) == 0
        assert len(diff['modified']) == 0
        assert len(diff['deleted']) == 1
        assert diff['deleted'][0]['clarifai_id'] == "clm_deleted"
    
    def test_parse_case_insensitive_comments(self):
        """Test that parsing is case-insensitive for HTML comments."""
        content = textwrap.dedent("""
        This is a test claim. <!-- CLARIFAI:ID=clm_upper VER=1 -->
        ^clm_upper
        
        Another claim. <!-- clarifai:id=clm_lower ver=2 -->
        ^clm_lower
        """).strip()
        
        blocks = self.parser.parse_content(content)
        
        assert len(blocks) == 2
        ids = [block.clarifai_id for block in blocks]
        assert "clm_upper" in ids
        assert "clm_lower" in ids
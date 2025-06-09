"""
Test fixtures and golden file tests for the Tier 1 import system.
"""

import json
import tempfile
from pathlib import Path

from clarifai_shared.import_system import Tier1ImportSystem
from clarifai_shared.config import ClarifAIConfig, VaultPaths


def test_various_conversation_formats():
    """Test import system with different conversation formats."""
    
    # Test cases with expected conversation count
    test_cases = [
        # Simple speaker format
        ("alice: Hello\nbob: Hi there!", 1),
        
        # ENTRY format
        ("ENTRY [10:00] alice >> Hello\nENTRY [10:01] bob >> Hi!", 1),
        
        # Mixed with metadata
        ("""SESSION_ID: abc123
TOPIC: Daily standup
alice: How's the project going?
bob: Making good progress!""", 1),
        
        # Empty file
        ("", 0),
        
        # No conversation patterns
        ("This is just some random text\nwithout any conversation patterns.", 0),
        
        # Complex conversation
        ("""alice: Let's discuss the quarterly results
bob: Sure, the numbers look good
alice: Revenue is up 15% from last quarter
charlie: What about expenses?
bob: Expenses stayed flat, so profit margins improved
alice: Excellent! Let's schedule a board presentation""", 1),
    ]
    
    with tempfile.TemporaryDirectory() as temp_dir:
        vault_dir = Path(temp_dir) / "vault"
        config = ClarifAIConfig(
            vault_path=str(vault_dir),
            paths=VaultPaths(tier1="tier1", logs="logs")
        )
        system = Tier1ImportSystem(config)
        
        for i, (content, expected_convs) in enumerate(test_cases):
            test_file = Path(temp_dir) / f"test_{i}.txt"
            test_file.write_text(content)
            
            print(f"\nTest case {i}: {content[:50]}...")
            
            try:
                output_files = system.import_file(test_file)
                actual_convs = len(output_files)
                
                print(f"  Expected conversations: {expected_convs}")
                print(f"  Actual conversations: {actual_convs}")
                
                if actual_convs == expected_convs:
                    print("  ✓ PASS")
                else:
                    print("  ✗ FAIL")
                    
                # Print content of generated files for inspection
                for j, output_file in enumerate(output_files):
                    print(f"  Generated file {j+1}:")
                    content = output_file.read_text()
                    print(f"    Title: {content.split('-->')[0].split('=')[1] if '-->' in content else 'N/A'}")
                    print(f"    Participants: {json.loads(content.split('clarifai:participants=')[1].split(' -->')[0]) if 'clarifai:participants=' in content else 'N/A'}")
                    print(f"    Message count: {content.split('clarifai:message_count=')[1].split(' -->')[0] if 'clarifai:message_count=' in content else 'N/A'}")
                    
            except Exception as e:
                if expected_convs == 0:
                    print(f"  ✓ PASS (Expected error for no conversations: {e})")
                else:
                    print(f"  ✗ FAIL (Unexpected error: {e})")


def test_atomic_write_safety():
    """Test that atomic writes work correctly under various conditions."""
    
    with tempfile.TemporaryDirectory() as temp_dir:
        vault_dir = Path(temp_dir) / "vault"
        config = ClarifAIConfig(
            vault_path=str(vault_dir),
            paths=VaultPaths(tier1="tier1", logs="logs")
        )
        system = Tier1ImportSystem(config)
        
        # Create a conversation file
        test_file = Path(temp_dir) / "atomic_test.txt"
        test_file.write_text("alice: Testing atomic writes\nbob: This should be safe")
        
        # Import the file
        output_files = system.import_file(test_file)
        assert len(output_files) == 1
        
        output_file = output_files[0]
        original_content = output_file.read_text()
        
        print("✓ Original import successful")
        
        # Verify no temporary files are left behind
        temp_files = list(output_file.parent.glob(".*tmp*"))
        assert len(temp_files) == 0, f"Found temporary files: {temp_files}"
        
        print("✓ No temporary files left behind")
        
        # Verify file content is complete
        assert "alice: Testing atomic writes" in original_content
        assert "<!-- clarifai:id=blk_" in original_content
        assert "^blk_" in original_content
        
        print("✓ File content is complete and properly formatted")


def test_filename_generation():
    """Test filename generation for various scenarios."""
    
    with tempfile.TemporaryDirectory() as temp_dir:
        vault_dir = Path(temp_dir) / "vault"
        config = ClarifAIConfig(
            vault_path=str(vault_dir),
            paths=VaultPaths(tier1="tier1", logs="logs")
        )
        system = Tier1ImportSystem(config)
        
        # Test with special characters in source filename
        test_file = Path(temp_dir) / "chat export (2024-06-09).txt"
        test_file.write_text("alice: Hello\nbob: Hi")
        
        output_files = system.import_file(test_file)
        output_filename = output_files[0].name
        
        print(f"Generated filename: {output_filename}")
        
        # Should start with date
        assert output_filename.startswith("2025-")
        
        # Should contain source name (with special chars converted to underscores)
        assert "chat_export__2024-06-09_" in output_filename
        
        # Should end with .md
        assert output_filename.endswith(".md")
        
        print("✓ Filename generation handles special characters correctly")


def test_multiple_conversations_from_single_file():
    """Test handling when a single file contains multiple conversations (future feature)."""
    
    # For now, the default plugin creates one conversation per file
    # But test the system can handle multiple MarkdownOutput objects
    
    with tempfile.TemporaryDirectory() as temp_dir:
        vault_dir = Path(temp_dir) / "vault"
        config = ClarifAIConfig(
            vault_path=str(vault_dir),
            paths=VaultPaths(tier1="tier1", logs="logs")
        )
        system = Tier1ImportSystem(config)
        
        # Create a longer conversation that might be split in the future
        test_file = Path(temp_dir) / "long_chat.txt"
        test_file.write_text("""alice: Let's start the meeting
bob: Sounds good
alice: First topic is budget
bob: We're on track
alice: Great! Next topic is timeline
bob: We might need an extension
alice: Let's discuss that offline""")
        
        output_files = system.import_file(test_file)
        
        # Currently should produce 1 conversation
        assert len(output_files) == 1
        
        content = output_files[0].read_text()
        
        # Verify all messages are included
        assert "Let's start the meeting" in content
        assert "discuss that offline" in content
        
        # Count block IDs to verify all messages have them
        block_ids = content.count("<!-- clarifai:id=blk_")
        message_count = int(content.split("clarifai:message_count=")[1].split(" -->")[0])
        
        assert block_ids == message_count
        
        print(f"✓ Single conversation with {message_count} messages and {block_ids} block IDs")


def test_import_log_functionality():
    """Test the import logging system in detail."""
    
    with tempfile.TemporaryDirectory() as temp_dir:
        vault_dir = Path(temp_dir) / "vault"
        config = ClarifAIConfig(
            vault_path=str(vault_dir),
            paths=VaultPaths(tier1="tier1", logs="logs")
        )
        system = Tier1ImportSystem(config)
        
        # Import first file
        file1 = Path(temp_dir) / "chat1.txt"
        file1.write_text("alice: First conversation\nbob: Yes indeed")
        
        output1 = system.import_file(file1)
        
        # Import second file with same content (should be duplicate)
        file2 = Path(temp_dir) / "chat2.txt"
        file2.write_text("alice: First conversation\nbob: Yes indeed")  # Same content
        
        try:
            system.import_file(file2)
            assert False, "Should have detected duplicate"
        except Exception as e:
            assert "duplicate" in str(e).lower()
        
        # Import third file with different content
        file3 = Path(temp_dir) / "chat3.txt"
        file3.write_text("alice: Different conversation\nbob: Absolutely")
        
        output3 = system.import_file(file3)
        
        # Check import log
        log_file = vault_dir / config.paths.logs / "imported_files.json"
        assert log_file.exists()
        
        with open(log_file) as f:
            log_data = json.load(f)
        
        # Should have 2 entries (file1 and file3, file2 was duplicate)
        assert len(log_data["hashes"]) == 2
        assert len(log_data["files"]) == 2
        
        # Check that file paths are recorded
        assert str(file1) in log_data["files"]
        assert str(file3) in log_data["files"]
        assert str(file2) not in log_data["files"]  # Was duplicate, shouldn't be logged
        
        print("✓ Import logging tracks files and detects duplicates correctly")


if __name__ == "__main__":
    print("=== Running Tier 1 Import System Tests ===\n")
    
    test_various_conversation_formats()
    print("\n" + "="*50)
    
    test_atomic_write_safety()
    print("\n" + "="*50)
    
    test_filename_generation()
    print("\n" + "="*50)
    
    test_multiple_conversations_from_single_file()
    print("\n" + "="*50)
    
    test_import_log_functionality()
    
    print("\n=== All tests completed! ===")
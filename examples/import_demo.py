#!/usr/bin/env python3
"""
Example script demonstrating the Tier 1 import system.

This script creates sample conversation files and imports them to show
the complete import pipeline in action.
"""

import tempfile
from pathlib import Path
from clarifai_shared import Tier1ImportSystem, ClarifAIConfig, VaultPaths

def create_sample_conversations(base_dir: Path):
    """Create sample conversation files for demonstration."""
    
    # Simple conversation
    simple_chat = base_dir / "simple_chat.txt"
    simple_chat.write_text("""alice: Hey, how's your day going?
bob: Pretty good! Just finished the quarterly report.
alice: Awesome! How did the numbers look?
bob: Revenue is up 12% from last quarter.
alice: That's fantastic news!""")
    
    # Meeting transcript with metadata
    meeting_log = base_dir / "team_meeting.txt"
    meeting_log.write_text("""SESSION_ID: team_weekly_20250609
TOPIC: Weekly Team Sync
PARTICIPANTS: alice, bob, charlie
START_TIME: 2025-06-09T10:00:00

alice: Let's start with project updates
bob: The backend API is 90% complete
charlie: Frontend is ready for testing
alice: Great! Any blockers?
bob: We need the database migration reviewed
charlie: I can help with that this afternoon
alice: Perfect. Next topic is the client demo
bob: Scheduled for Friday at 2 PM
charlie: All demo data is prepared
alice: Excellent work everyone!""")
    
    # Custom ENTRY format
    chat_export = base_dir / "chat_export.log"
    chat_export.write_text("""EXPORT_FORMAT: Custom Chat Log v1.0
DURATION: 00:15:30

ENTRY [14:30:15] sarah >> Hi everyone, ready for the standup?
ENTRY [14:30:22] mike >> Yes, let me share my screen
ENTRY [14:30:35] sarah >> Go ahead
ENTRY [14:30:45] mike >> Completed the user authentication module
ENTRY [14:31:00] sarah >> Any issues?
ENTRY [14:31:05] mike >> None, all tests passing
ENTRY [14:31:15] sarah >> Great! What's next?
ENTRY [14:31:25] mike >> Working on payment integration""")
    
    # Non-conversation file (should be skipped)
    random_file = base_dir / "random_notes.txt"
    random_file.write_text("""These are just some random notes
that don't contain any conversation patterns.

- Remember to update the documentation
- Check the test coverage
- Review the pull requests

This file should not generate any Tier 1 output.""")
    
    return [simple_chat, meeting_log, chat_export, random_file]

def main():
    """Run the demonstration."""
    print("🚀 ClarifAI Tier 1 Import System Demo")
    print("="*50)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Setup directories
        input_dir = temp_path / "conversations"
        input_dir.mkdir()
        vault_dir = temp_path / "vault"
        
        print(f"📁 Demo directories:")
        print(f"  Input: {input_dir}")
        print(f"  Vault: {vault_dir}")
        print()
        
        # Create sample files
        print("📝 Creating sample conversation files...")
        sample_files = create_sample_conversations(input_dir)
        for file in sample_files:
            print(f"  ✓ {file.name}")
        print()
        
        # Initialize import system
        config = ClarifAIConfig(
            vault_path=str(vault_dir),
            paths=VaultPaths(
                tier1="conversations",
                logs="import_logs"
            )
        )
        system = Tier1ImportSystem(config)
        print("✅ Import system initialized")
        print()
        
        # Import files
        print("📥 Importing conversation files...")
        results = system.import_directory(input_dir, recursive=False)
        print()
        
        # Display results
        print("📊 Import Results:")
        total_files = len(results)
        successful = sum(1 for files in results.values() if files)
        skipped = sum(1 for files in results.values() if not files)
        
        print(f"  Total files processed: {total_files}")
        print(f"  Successful imports: {successful}")
        print(f"  Skipped (no conversations): {skipped}")
        print()
        
        # Show generated files
        tier1_dir = vault_dir / "conversations"
        if tier1_dir.exists():
            tier1_files = list(tier1_dir.glob("*.md"))
            print(f"📄 Generated Tier 1 files ({len(tier1_files)}):")
            for file in tier1_files:
                print(f"  ✓ {file.name}")
            print()
            
            # Show content of first file
            if tier1_files:
                first_file = tier1_files[0]
                print(f"📖 Sample content from {first_file.name}:")
                print("─" * 60)
                content = first_file.read_text()
                lines = content.split('\n')
                # Show first 15 lines
                for line in lines[:15]:
                    print(line)
                if len(lines) > 15:
                    print("...")
                print("─" * 60)
                print()
        
        # Show import log
        log_file = vault_dir / "import_logs" / "imported_files.json"
        if log_file.exists():
            print("📋 Import log created:")
            print(f"  {log_file}")
            import json
            with open(log_file) as f:
                log_data = json.load(f)
            print(f"  Tracked {len(log_data['hashes'])} unique files")
            print()
        
        # Test duplicate detection
        print("🔄 Testing duplicate detection...")
        try:
            # Try to import the same directory again
            results_2 = system.import_directory(input_dir, recursive=False)
            duplicates = sum(1 for source, files in results_2.items() if not files)
            print(f"  ✓ Detected {duplicates} duplicates (skipped)")
        except Exception as e:
            print(f"  ✗ Duplicate detection failed: {e}")
        print()
        
        print("🎉 Demo completed successfully!")
        print(f"💡 Try running with --vault-path {vault_dir} to see persistent results")

if __name__ == "__main__":
    main()
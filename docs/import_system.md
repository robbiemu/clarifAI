# Tier 1 Markdown Import System

The Tier 1 import system provides a complete pipeline for importing conversation files into the ClarifAI vault as standardized Tier 1 Markdown documents.

## Features

- **Hash-based duplicate detection**: SHA-256 hashing prevents re-importing the same content
- **Plugin-based format conversion**: Extensible system supports multiple conversation formats
- **Atomic file writing**: Safe `.tmp` → `fsync` → `rename` pattern prevents corruption
- **Proper Tier 1 format**: Generates compliant Markdown with metadata and block annotations
- **Configuration-driven**: Uses vault paths from central configuration
- **Import logging**: Tracks successful imports for auditing and duplicate detection

## Usage

### Programmatic Usage

```python
from clarifai_shared import Tier1ImportSystem, ClarifAIConfig, VaultPaths

# Initialize with configuration
config = ClarifAIConfig(
    vault_path="/path/to/vault",
    paths=VaultPaths(tier1="conversations", logs="logs")
)
system = Tier1ImportSystem(config)

# Import a single file
output_files = system.import_file("chat_export.txt")
print(f"Created {len(output_files)} Tier 1 files")

# Import a directory
results = system.import_directory("exports/", recursive=True)
```

### Command Line Usage

```bash
# Import a single file
python -m clarifai_shared.import_cli --file chat_export.txt

# Import all files from a directory
python -m clarifai_shared.import_cli --directory exports/

# Import with custom vault path
python -m clarifai_shared.import_cli --file chat.txt --vault-path /custom/vault

# Verbose logging
python -m clarifai_shared.import_cli --file chat.txt --verbose
```

## Configuration

The import system uses the following configuration:

```python
@dataclass
class VaultPaths:
    tier1: str = "tier1"          # Where to write Tier 1 Markdown files
    summaries: str = "."          # Where to write Tier 2 summaries (future)
    concepts: str = "."           # Where to write Tier 3 concepts (future)  
    logs: str = ".clarifai/import_logs"  # Import logging directory
```

Environment variables:
- `VAULT_PATH`: Base vault directory
- `VAULT_TIER1_PATH`: Tier 1 subdirectory (default: "tier1")
- `VAULT_LOGS_PATH`: Logs subdirectory (default: ".clarifai/import_logs")

## Generated Format

The system generates Tier 1 Markdown files following this format:

```markdown
<!-- clarifai:title=Conversation between alice, bob -->
<!-- clarifai:created_at=2025-06-09T23:23:54.614123 -->
<!-- clarifai:participants=["alice", "bob"] -->
<!-- clarifai:message_count=3 -->
<!-- clarifai:plugin_metadata={"source_format": "fallback_llm", "original_format": "unknown"} -->

alice: Hello there!
<!-- clarifai:id=blk_k5ly50 ver=1 -->
^blk_k5ly50

bob: Hi Alice, how are you?
<!-- clarifai:id=blk_xe5381 ver=1 -->
^blk_xe5381

alice: I'm doing great, thanks for asking!
<!-- clarifai:id=blk_mibham ver=1 -->
^blk_mibham
```

### Format Elements

- **File-level metadata**: HTML comments at the top with conversation metadata
- **Block-level annotations**: Each utterance gets a unique `clarifai:id` and Obsidian `^anchor`
- **Deterministic IDs**: Block IDs are generated deterministically for consistency
- **Version tracking**: `ver=1` indicates first version (for future updates)

## Supported Input Formats

The system supports various conversation formats through the plugin system:

### Simple Speaker Format
```
alice: Hello, how are you?
bob: I'm doing well, thanks!
```

### ENTRY Format (Custom Logs)
```
ENTRY [10:00:00] alice >> Let's start the meeting.
ENTRY [10:00:30] bob >> I've prepared the agenda.
```

### With Metadata
```
SESSION_ID: abc123
TOPIC: Daily standup
alice: How's the project going?
bob: Making good progress!
```

## Duplicate Detection

The system calculates SHA-256 hashes of input file content and maintains an import log:

```json
{
  "hashes": {
    "c50b2a66e1760a8f...": {
      "source_file": "/path/to/chat.txt",
      "imported_at": "2025-06-09T23:24:03.172263",
      "output_files": ["/vault/tier1/2025-06-09_chat_Conversation.md"]
    }
  },
  "files": {
    "/path/to/chat.txt": {
      "hash": "c50b2a66e1760a8f...",
      "imported_at": "2025-06-09T23:24:03.172263", 
      "output_files": ["/vault/tier1/2025-06-09_chat_Conversation.md"]
    }
  }
}
```

## File Naming

Output files use a canonical naming scheme:
- Format: `YYYY-MM-DD_{source_name}_{conversation_title}.md`
- Special characters in filenames are converted to underscores
- Date is extracted from conversation metadata or file modification time

## Error Handling

The system implements robust error handling:

- **DuplicateDetectionError**: Raised when a file is detected as a duplicate
- **ImportSystemError**: General import failures (file not found, permission errors, etc.)
- **UnknownFormatError**: When no plugin can handle the input format
- **Graceful fallback**: LLM failures fall back to pattern matching

## Atomic Writes

All file operations use atomic writes to prevent corruption:

1. Write content to `.tmp` file in same directory  
2. Call `fsync()` to ensure data is written to disk
3. Atomically rename `.tmp` file to final name
4. Clean up temporary files on any failure

This ensures other processes (like Obsidian) never see partially written files.

## Testing

The system includes comprehensive tests:

```bash
# Basic functionality test
python shared/tests/test_tier1_import.py

# Comprehensive test suite
python shared/tests/test_tier1_comprehensive.py
```

Tests cover:
- Various conversation formats
- Duplicate detection
- Atomic write safety  
- Filename generation
- Error handling
- Import logging

## Architecture Integration

The import system integrates with ClarifAI's broader architecture:

- **Plugin System**: Uses existing plugin interface and default plugin
- **Configuration**: Leverages central configuration system
- **Vault Structure**: Respects configured directory layout
- **Graph Sync**: Generated files are ready for graph synchronization
- **Obsidian Compatibility**: Safe concurrent access with Obsidian

The system implements the requirements from:
- `docs/project/epic_1/sprint_2-Create_Tier_1_Markdown.md`
- `docs/arch/idea-creating_tier1_documents.md`
- `docs/arch/on-pluggable_formats.md`
- `docs/arch/on-filehandle_conflicts.md`
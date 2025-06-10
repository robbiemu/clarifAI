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

For complete usage examples and step-by-step tutorials, see:
- **Tutorial**: `docs/tutorials/tier1_import_tutorial.md` - Complete guide with examples
- **CLI Reference**: `shared/clarifai_shared/scripts/import_cli.py --help` - Command line options

## Configuration

The import system uses the central `ClarifAIConfig` system with vault path configuration. See `shared/clarifai_shared/config.py` for the `VaultPaths` dataclass implementation and `docs/ENVIRONMENT_CONFIGURATION.md` for environment variable details.

## Generated Format

The system generates Tier 1 Markdown files with proper file-level metadata, block annotations, and Obsidian-compatible anchors. For detailed format specifications and examples, see `docs/tutorials/tier1_import_tutorial.md`.

## Supported Input Formats

The system supports various conversation formats through the pluggable format conversion system. See `docs/arch/on-pluggable_formats.md` for details on the plugin architecture and `MarkdownOutput` structure.

## Duplicate Detection

The system uses SHA-256 content hashing for duplicate detection and maintains import logs in JSON format. For usage examples, see `docs/tutorials/tier1_import_tutorial.md`.

## File Naming

Output files use a canonical naming scheme:
- Format: `YYYY-MM-DD_{source_name}_{conversation_title}.md`
- Special characters in filenames are converted to underscores
- Date is extracted from conversation metadata or file modification time

## Error Handling

The system implements robust error handling with specific exception types for different failure modes. For usage examples and error handling patterns, see `docs/tutorials/tier1_import_tutorial.md`. For architectural details on atomic write safety, see `docs/arch/on-filehandle_conflicts.md`.

## Testing

The system includes comprehensive test coverage. See test files in `shared/tests/` for implementation details and `shared/tests/test_tier1_*.py` for running specific test suites.

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
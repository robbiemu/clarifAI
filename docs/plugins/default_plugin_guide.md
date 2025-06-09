# Default Plugin Implementation Guide

This document describes the implementation of the default/fallback plugin for ClarifAI's pluggable format conversion system.

## Overview

The default plugin serves as a fallback for files that aren't recognized by specific format plugins. It uses pattern matching and optional LLM processing to extract conversations from unstructured text and convert them to ClarifAI's standard Tier 1 Markdown format.

## Architecture

### Plugin System Components

The plugin system consists of several key components in the `clarifai_shared` package:

#### 1. Plugin Interface (`plugin_interface.py`)
- `Plugin` abstract base class defining the plugin interface
- `MarkdownOutput` dataclass for plugin output
- `UnknownFormatError` exception for unsupported formats

#### 2. Plugin Utilities (`plugins/utils.py`)
- `ensure_defaults()` function to fill missing metadata
- `convert_file_to_markdowns()` orchestrator function

#### 3. Default Plugin (`plugins/default_plugin.py`)
- `DefaultPlugin` class implementing the fallback behavior
- `ConversationExtractorAgent` for LLM-based extraction

## Usage

### Basic Usage

```python
from clarifai_shared import DefaultPlugin, convert_file_to_markdowns
from pathlib import Path

# Create plugin instance
plugin = DefaultPlugin()

# Create plugin registry (in real usage, include other plugins first)
registry = [plugin]

# Convert a file
input_file = Path("conversation.txt")
outputs = convert_file_to_markdowns(input_file, registry)

for output in outputs:
    print(f"Title: {output.title}")
    print(f"Participants: {output.metadata['participants']}")
    print(output.markdown_text)
```

### Integration with Orchestrator

The default plugin is designed to be used as the last plugin in the orchestrator's plugin registry:

```python
# Typical orchestrator setup
registry = [
    ChatGPTPlugin(),      # Specific format plugins first
    SlackPlugin(),
    WhatsAppPlugin(),
    DefaultPlugin()       # Fallback plugin last
]

# The orchestrator tries each plugin until one accepts the input
outputs = convert_file_to_markdowns(input_file, registry)
```

## Supported Formats

The default plugin can handle various conversation formats through pattern matching:

### 1. Simple Speaker Format
```
alice: Hello, how are you?
bob: I'm doing well, thanks!
alice: That's great to hear.
```

### 2. ENTRY Format (Custom Logs)
```
ENTRY [10:00:00] alice >> Let's start the meeting.
ENTRY [10:00:30] bob >> I've prepared the agenda.
ENTRY [10:01:00] alice >> Perfect, let's begin.
```

### 3. Metadata Extraction

The plugin automatically extracts metadata from common fields:
- `SESSION_ID:` → session identifier
- `TOPIC:` → conversation title
- `DURATION:` → conversation duration
- `EXPORT_FORMAT:` → original format information

## Output Format

The plugin generates ClarifAI Tier 1 Markdown with the following structure:

```markdown
<!-- clarifai:title=Conversation Title -->
<!-- clarifai:created_at=2023-12-22T16:45:00Z -->
<!-- clarifai:participants=["alice", "bob"] -->
<!-- clarifai:message_count=3 -->
<!-- clarifai:plugin_metadata={"source_format": "fallback_llm", ...} -->

alice: First message content
<!-- clarifai:id=blk_abc123 ver=1 -->
^blk_abc123

bob: Second message content
<!-- clarifai:id=blk_def456 ver=1 -->
^blk_def456

<!-- clarifai:entailed_score=0.86 -->
<!-- clarifai:coverage_score=0.79 -->
<!-- clarifai:decontextualization_score=0.83 -->
```

### Metadata Fields

| Field | Description | Default |
|-------|-------------|---------|
| `title` | Conversation title | Auto-generated from timestamp |
| `created_at` | ISO timestamp | File modification time |
| `participants` | List of speakers | Extracted from content |
| `message_count` | Number of messages | Count of extracted messages |
| `plugin_metadata` | Plugin-specific data | Includes source format info |

### Block IDs

Each message receives a unique block ID in the format `blk_xxxxxx` where `xxxxxx` is a 6-character alphanumeric string. Block IDs are:
- Unique within each conversation
- Referenced both in comments and anchor links
- Used for claim extraction and linking in later processing

## LLM Integration

The plugin supports optional LLM integration for enhanced conversation extraction:

### Configuration

Set environment variables for LLM access:
```bash
export OPENAI_API_KEY="your-api-key-here"
```

### Fallback Behavior

When LLM is unavailable or fails:
1. Plugin falls back to pattern-matching extraction
2. Uses regex patterns for common conversation formats
3. Gracefully handles extraction failures

## Testing

The plugin includes comprehensive test coverage:

```bash
# Run plugin system tests
pytest shared/tests/test_plugins.py -v

# Run default plugin specific tests
pytest shared/tests/test_default_plugin.py -v
```

### Test Coverage

- Plugin interface compliance
- Metadata generation and defaults
- Pattern matching for various formats
- Block ID uniqueness
- Error handling and fallback behavior
- Integration with orchestrator

## Performance Considerations

### Pattern Matching
- Fast fallback for common formats
- No external dependencies required
- Handles large files efficiently

### LLM Processing
- Optional enhancement for complex formats
- Configurable timeout and retry logic
- Graceful degradation when unavailable

### Memory Usage
- Processes files in memory
- Suitable for typical conversation file sizes
- Consider chunking for very large files

## Error Handling

The plugin implements robust error handling:

1. **Format Detection**: Always returns `True` from `can_accept()`
2. **Extraction Failures**: Returns empty list if no conversation found
3. **LLM Failures**: Falls back to pattern matching
4. **Invalid Input**: Handles malformed or empty files gracefully

## Extension Points

### Custom Patterns

Add new conversation patterns by extending the regex patterns in `_fallback_extraction()`:

```python
# Add custom pattern
custom_pattern = r'^(\w+)\s*says:\s*(.+)$'

if re.match(custom_pattern, line):
    # Handle custom format
    pass
```

### LLM Models

Support different LLM providers by extending `ConversationExtractorAgent`:

```python
from llama_index.llms.anthropic import Anthropic

agent = ConversationExtractorAgent(
    llm=Anthropic(api_key="your-key")
)
```

### Metadata Extraction

Add custom metadata extraction in `_extract_metadata()`:

```python
# Extract custom fields
if 'CUSTOM_FIELD:' in line:
    metadata["custom_field"] = line.split('CUSTOM_FIELD:')[1].strip()
```

## Integration with Sprint 8

The default plugin is designed to integrate seamlessly with the plugin manager and orchestrator from Sprint 8:

1. **Plugin Discovery**: Implements the standard `Plugin` interface
2. **Registry Integration**: Can be added to any plugin registry
3. **Error Propagation**: Compatible with orchestrator error handling
4. **Logging**: Uses structured logging for debugging

## Future Enhancements

Potential improvements for future versions:

1. **Chunking**: Support for very large files
2. **Language Detection**: Multi-language conversation support
3. **Format Hints**: User-provided format hints for better extraction
4. **Caching**: Cache LLM responses for similar content
5. **Streaming**: Support for real-time conversation processing

## Troubleshooting

### Common Issues

**No conversations extracted:**
- Check input format matches supported patterns
- Verify speaker names are valid identifiers
- Ensure messages have clear speaker/text separation

**LLM errors:**
- Verify API key configuration
- Check network connectivity
- Review rate limiting and quotas

**Performance issues:**
- Consider disabling LLM for large batch processing
- Use pattern matching only for simple formats
- Monitor memory usage with very large files

### Debug Mode

Enable debug logging to troubleshoot extraction issues:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Plugin operations will now log detailed information
```
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
```

### Metadata Fields

| Field | Description | Default | Consumer |
|-------|-------------|---------|----------|
| `title` | Conversation title | Auto-generated from timestamp | UI display, file naming |
| `created_at` | ISO timestamp | File modification time | Chronological sorting |
| `participants` | List of speakers | Extracted from content | Participant analysis |
| `message_count` | Number of messages | Count of extracted messages | Content filtering |
| `plugin_metadata` | Plugin-specific data | See below | Plugin orchestrator, debugging |

### Plugin Metadata Structure

The `plugin_metadata` field contains information about how the conversation was processed:

```json
{
  "source_format": "fallback_llm",          // Processing method used
  "extraction_method": "procedural",        // "procedural" or "llm"
  "original_format": "Custom_LOG_v2.1",     // Detected original format
  "session_id": "sess_123abc",              // Extracted session ID
  "duration": "5m0s",                       // Conversation duration
  "block_count": 3,                         // Number of blocks generated
  "processing_notes": "Used ENTRY pattern"  // Additional processing info
}
```

**Default Plugin Fields:**
- `source_format`: Always "fallback_llm" to indicate default plugin processing
- `extraction_method`: "procedural" (pattern matching) or "llm" (AI processing)
- `original_format`: Original format identifier if detected from metadata
- `session_id`: Session identifier extracted from log headers
- `duration`: Conversation duration from metadata
- `block_count`: Number of message blocks generated
- `processing_notes`: Additional context about extraction process

**Downstream Consumption:**
- **Plugin Orchestrator**: Uses `source_format` to track which plugin processed the file
- **UI Components**: Display `extraction_method` to show processing approach (⚠️ Fallback indicator)
- **Quality Analysis**: Uses extraction metadata for processing quality assessment
- **Debugging**: `processing_notes` help troubleshoot conversion issues

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

### Processing Flow

The plugin uses an optimized extraction strategy:
1. **Procedural extraction first**: Attempts pattern matching for common formats (fast, reliable, no cost)
2. **LLM fallback**: Only uses LLM processing when procedural extraction finds no conversations
3. **Graceful degradation**: Returns empty list if both approaches fail

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

### YAML Prompt Configuration

The default plugin uses externalized YAML prompt templates that can be customized by users. This allows fine-tuning of the LLM behavior without modifying code.

#### Default Installation

During installation or Docker container startup, default prompt templates are automatically installed to the `prompts/` directory:

```bash
# Automatically creates prompts/conversation_extraction.yaml
python install_prompts.py

# Install all available prompts
python install_prompts.py --all

# Force overwrite existing prompts (restore defaults)
python install_prompts.py --force
```

#### Customizing Prompts

The main prompt template is located at `prompts/conversation_extraction.yaml`:

```yaml
role: "conversation_extraction_agent"
description: "Analyzes unstructured text to extract conversations"
system_prompt: "You are an expert conversation analyst..."
template: |
  Analyze the following text and extract conversations.
  
  Instructions:
  - Look for dialogue patterns between participants
  - Extract speaker names and their messages
  - If no conversation found, respond with "NO_CONVERSATION"
  
  TEXT TO ANALYZE:
  {input_text}
  
output_format: "JSON format with title, participants, and messages"
variables:
  input_text:
    description: "Raw text content to analyze"
    required: true
rules:
  - "Maintain speaker attribution accuracy"
  - "Preserve message content and context"
  - "Generate appropriate conversation titles"
```

#### Template Variables

The conversation extraction template supports these variables:

| Variable | Required | Description |
|----------|----------|-------------|
| `input_text` | Yes | The raw text content to analyze for conversations |

#### Prompt Customization Examples

**For Technical Discussions:**
```yaml
# Modify the template section to focus on technical content
template: |
  Analyze this technical discussion and extract conversations.
  Focus on:
  - Code review comments
  - Technical questions and answers
  - Bug reports and solutions
  
  Content: {input_text}
```

**For Meeting Transcripts:**
```yaml
# Customize for formal meeting formats
template: |
  Extract conversations from this meeting transcript.
  Preserve:
  - Action items and decisions
  - Participant roles and context
  - Time-sensitive discussions
  
  Transcript: {input_text}
```

#### Docker Configuration

In Docker environments, prompt files are automatically installed and mounted as volumes for persistence:

```dockerfile
# Automatically installs prompts during build
RUN python install_prompts.py --all

# Mount prompts directory for user customization
VOLUME ["/app/prompts"]
```

Users can then:
1. Copy prompt files from the container: `docker cp container:/app/prompts ./prompts`
2. Edit the YAML files locally
3. Mount the directory back: `docker run -v ./prompts:/app/prompts clarifai`

#### Troubleshooting

**Restore Default Prompts:**
```bash
# Delete customized file and restart service
rm prompts/conversation_extraction.yaml
# Service will auto-install default on next run

# Or force reinstall
python install_prompts.py --force
```

**Validate YAML Syntax:**
```bash
# Check if your YAML is valid
python -c "import yaml; yaml.safe_load(open('prompts/conversation_extraction.yaml'))"
```

### LLM Configuration

The plugin supports transparent LLM configuration through the ClarifAI configuration system:

```python
# LLM configuration is handled automatically through the config system
# The plugin will use the configured model for model.fallback_plugin role
plugin = DefaultPlugin()

# For custom configurations, you can create an agent with specific LLM
from clarifai_shared.plugins.default_plugin import ConversationExtractorAgent

# The agent will automatically use the configured LLM
agent = ConversationExtractorAgent()
```

**Configuration Notes:**
- LLM selection is managed through `settings/clarifai.config.yaml` 
- The `model.fallback_plugin` configuration determines which LLM to use
- Supports multiple providers: OpenAI, Anthropic, Ollama, OpenRouter
- No hardcoded model dependencies in plugin code

## Usage as Fallback Plugin

The default plugin is designed to be used as the last plugin in the orchestrator's plugin registry, providing fallback processing for unrecognized formats:

```python
# Proper orchestrator integration
registry = [
    ChatGPTPlugin(),      # Format-specific plugins first
    SlackPlugin(),
    WhatsAppPlugin(),
    DefaultPlugin()       # Fallback plugin last
]
```

The plugin should **not** be used as a template for custom plugin development. Instead, refer to the plugin interface documentation and use the shared utilities provided in the `clarifai_shared.utils` module.

## Integration with Plugin System

The default plugin is designed to integrate seamlessly with the plugin manager and orchestrator:

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
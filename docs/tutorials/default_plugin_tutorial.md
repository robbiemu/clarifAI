# Getting Started with ClarifAI Default Plugin

This tutorial walks you through using ClarifAI's default plugin for converting unstructured conversation data into standardized Tier 1 Markdown format. The default plugin serves as a fallback for files that aren't recognized by specific format plugins.

## Overview

The default plugin is part of ClarifAI's pluggable format conversion system. It:
- Always accepts input as a fallback option
- Uses pattern matching and optional LLM processing
- Converts conversations to ClarifAI Tier 1 Markdown format
- Generates unique block IDs and metadata

## Step 1: Basic Setup

First, let's set up the basic imports and plugin registry:

```python
import sys
import tempfile
from pathlib import Path

# Add the shared module to the path
sys.path.append(str(Path(__file__).parent / "shared"))

# Import the plugin system
from clarifai_shared import DefaultPlugin, convert_file_to_markdowns
```

## Step 2: Prepare Sample Data

The default plugin can handle various conversation formats. Let's start with a custom log format:

```python
sample_data = """
CONVERSATION_LOG_v1.0
====================
SESSION_ID: demo_001
TOPIC: Sprint Planning
PARTICIPANTS: alice, bob, charlie

ENTRY [09:00:00] alice >> Let's start our sprint planning meeting.
ENTRY [09:00:15] bob >> I've prepared the backlog for review.
ENTRY [09:00:30] charlie >> Great! I see we have 15 user stories to estimate.
ENTRY [09:01:00] alice >> Let's start with the authentication improvements.
ENTRY [09:01:20] bob >> That should be a 3-point story based on complexity.
ENTRY [09:01:45] charlie >> I agree. It touches multiple components but the scope is clear.

SESSION_END: 09:05:00
DURATION: 5m0s
"""
```

## Step 3: Process with Default Plugin

Create a plugin registry and process the conversation:

```python
# Create a temporary file with the sample data
with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".log") as f:
    f.write(sample_data)
    temp_path = Path(f.name)

try:
    # Create plugin registry with the default plugin
    default_plugin = DefaultPlugin()
    registry = [default_plugin]

    print("Processing with DefaultPlugin...")

    # Convert the file
    outputs = convert_file_to_markdowns(temp_path, registry)

    print(f"✅ Successfully processed file!")
    print(f"📊 Extracted {len(outputs)} conversation(s)")

finally:
    # Clean up
    temp_path.unlink()
```

## Step 4: Examine the Results

Let's look at what the plugin extracted:

```python
if outputs:
    output = outputs[0]
    print(f"📝 Conversation Details:")
    print(f"   Title: {output.title}")
    print(f"   Participants: {output.metadata['participants']}")
    print(f"   Message Count: {output.metadata['message_count']}")
    print(f"   Plugin Used: {output.metadata['plugin_metadata']['source_format']}")

    print("📄 Generated Markdown:")
    print(output.markdown_text)
```

Expected output format:
```markdown
<!-- clarifai:title=Sprint Planning -->
<!-- clarifai:created_at=2023-12-22T16:45:00Z -->
<!-- clarifai:participants=["alice", "bob", "charlie"] -->
<!-- clarifai:message_count=6 -->
<!-- clarifai:plugin_metadata={"source_format": "fallback_llm", ...} -->

alice: Let's start our sprint planning meeting.
<!-- clarifai:id=blk_abc123 ver=1 -->
^blk_abc123

bob: I've prepared the backlog for review.
<!-- clarifai:id=blk_def456 ver=1 -->
^blk_def456

...
```

## Step 5: Try Different Formats

The default plugin handles multiple conversation formats:

### Simple Speaker Format
```python
simple_conversation = """
john: Hey, how's the project going?
jane: Pretty well! We're ahead of schedule.
john: That's great news. Any blockers?
jane: Just waiting on the design review.
"""
```

### JSON Format
```python
json_conversation = """
{
  "messages": [
    {"speaker": "alice", "text": "Hello everyone"},
    {"speaker": "bob", "text": "Hi Alice, ready for the meeting?"}
  ]
}
"""
```

### CSV Format
```python
csv_conversation = """
timestamp,speaker,message
09:00:00,alice,"Let's start the meeting"
09:00:15,bob,"I have the agenda ready"
"""
```

## Step 6: Understanding Plugin Behavior

The default plugin demonstrates key plugin interface behaviors:

```python
plugin = DefaultPlugin()

test_inputs = [
    "random text with no conversation",
    "alice: hello\nbob: hi there", 
    "ENTRY [10:00] speaker >> message",
    "",
    "1234567890 !@#$%^&*()",
]

print("Testing can_accept() method:")
for i, test_input in enumerate(test_inputs, 1):
    accepts = plugin.can_accept(test_input)
    print(f"  {i}. '{test_input[:30]}...' -> {accepts}")

# Output: All return True (fallback behavior)
```

## Step 7: Integration with Plugin System

In a real system, the default plugin works as part of a plugin registry:

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

When other plugins return `False` from `can_accept()`, the default plugin will always return `True` and attempt to extract conversations using its pattern matching and LLM capabilities.

## Key Features Demonstrated

- **Fallback Behavior**: Always accepts input when other plugins fail
- **Multiple Format Support**: Handles various conversation structures
- **Metadata Extraction**: Automatically extracts session IDs, topics, durations
- **Block ID Generation**: Creates unique identifiers for each message
- **Tier 1 Compliance**: Outputs standard ClarifAI Markdown format

## Next Steps

- Integrate with the full plugin orchestrator system
- Add more specific format plugins for common conversation types
- Configure LLM credentials for enhanced conversation extraction
- Explore writing custom plugins using the default plugin as a reference

## Writing Custom Plugins

The default plugin demonstrates the standard plugin interface. To write your own plugin:

1. **Inherit from Plugin base class**
2. **Implement can_accept()**: Return True/False based on format detection
3. **Implement convert()**: Extract conversations and return MarkdownOutput objects
4. **Use shared utilities**: Leverage block ID generation and metadata helpers

Example custom plugin structure:
```python
from clarifai_shared import Plugin, MarkdownOutput
from clarifai_shared.utils.block_id import generate_unique_block_id

class MyCustomPlugin(Plugin):
    def can_accept(self, raw_input: str) -> bool:
        # Check if this plugin can handle the input format
        return "MY_FORMAT_MARKER" in raw_input
    
    def convert(self, raw_input: str, file_path: Path) -> List[MarkdownOutput]:
        # Extract conversations and return formatted output
        # Use generate_unique_block_id() for block IDs
        pass
```

The default plugin serves as both a functional fallback and a comprehensive example for plugin development.
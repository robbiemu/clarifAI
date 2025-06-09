# Tier 1 Conversion Examples

This directory contains golden standard test data for Tier 1 conversion tasks, providing diverse raw conversation inputs and their corresponding expected Tier 1 Markdown output files.

## Purpose

These examples serve as consistent test data for verifying the correctness and robustness of:

- **Default Plugin Implementation**: Ensuring the LLM agent converts arbitrary input correctly
- **Tier 1 Markdown Creation**: Ensuring it correctly writes and annotates Markdown files with proper `clarifai:id` and `^anchor` format
- **Utterance Embedding**: Ensuring it correctly segments and embeds the generated Tier 1 Markdown

## Directory Structure

```
tier1_conversion_examples/
├── README.md                    # This file
├── inputs/                      # Raw conversation input files
│   ├── chatgpt_export.json     # Realistic ChatGPT export structure
│   ├── slack_export.csv        # Simplified CSV for testing (not realistic Slack format)
│   ├── plain_text_chat.txt     # Plain text conversation transcript
│   └── unrecognized_format.xyz # Mock format for LLM fallback testing
└── expected_outputs/            # Golden standard Tier 1 Markdown files
    ├── chatgpt_export.md
    ├── slack_export.md
    ├── plain_text_chat.md
    └── unrecognized_format.md
```

## Format Specifications and Assumptions

### Real-World Export Format Context

Before describing our test formats, it's important to understand how conversation platforms actually export data:

**Slack Export Reality:**
- Slack primarily exports data as JSON within ZIP archives containing hierarchical structures
- Comprehensive exports include `channels.json`, `users.json`, and daily message files (e.g., `2024-06-09.json`)
- CSV exports are limited to administrative data (channel audit reports, member listings) and do not include actual conversation content
- Message objects follow Slack's API format with fields like `type`, `user`, `text`, `ts`, `reactions`, etc.

**ChatGPT Export Reality:**
- ChatGPT exports provide a single `conversations.json` file within a ZIP archive
- Uses a tree-like mapping structure where conversations can branch into alternative response paths
- Each conversation contains a `mapping` field serving as a lookup table for message nodes
- Messages reference parent/child relationships enabling conversation reconstruction

### Test Format Assumptions and Trade-offs

Our test fixtures make deliberate format choices for comprehensive testing coverage:

### Input Files

- **chatgpt_export.json**: Follows actual ChatGPT export structure with `title`, `mapping`, and message nodes containing `author.role`, `content.parts`, etc. This represents realistic ChatGPT data.

- **slack_export.csv**: **Intentionally simplified CSV format for testing purposes**. While Slack doesn't export conversation content as CSV, we include this format to:
  - Test CSV parsing capabilities in our conversion pipeline
  - Provide a simple tabular format that other tools might export
  - Validate handling of timestamp, user_name, message column structures
  - Cover edge cases like reactions, thread handling in columnar data

- **plain_text_chat.txt**: Represents manual conversation transcripts or exports from platforms that provide simple text output with speaker prefixes.

- **unrecognized_format.xyz**: Mock format for testing LLM-based fallback parsing when no specific plugin matches the input format.

### Design Rationale

**Why These Format Choices:**

1. **Comprehensive Plugin Testing**: By including both realistic (ChatGPT JSON) and simplified (CSV) formats, we test both specific platform plugins and generic parsing capabilities.

2. **Edge Case Coverage**: The CSV format, while not realistic for Slack, allows us to test columnar data parsing that other tools or platforms might provide.

3. **LLM Fallback Validation**: The unrecognized format ensures our LLM-based default plugin can handle arbitrary conversation data when no specific parser matches.

4. **Progressive Complexity**: From simple text to complex JSON structures, the formats test different levels of parsing sophistication.

**Realistic Alternative**: If more platform-accurate testing is needed, `slack_export.csv` could be replaced with `slack_export.json` using actual Slack export structure:

```json
[
  {
    "type": "message",
    "user": "U0987654321",
    "text": "Hello everyone!",
    "ts": "1234567890.123456"
  }
]
```

However, the current CSV approach provides valuable tabular data parsing validation that complements the JSON-based formats.

### Expected Output Files
All Tier 1 Markdown outputs follow the standardized format:

1. **File-level HTML metadata comments** containing:
   - `title`: Conversation title
   - `created_at`: ISO timestamp
   - `participants`: List of speakers
   - `message_count`: Number of messages
   - `plugin_metadata`: Plugin-specific data

2. **Speaker utterance blocks** in format:
   ```markdown
   Speaker: Message text here
   <!-- clarifai:id=blk_abc123 ver=1 -->
   ^blk_abc123
   ```

3. **Evaluation scores** (for testing evaluation integration):
   ```markdown
   <!-- clarifai:entailed_score=0.91 -->
   <!-- clarifai:coverage_score=0.77 -->
   <!-- clarifai:decontextualization_score=0.88 -->
   ```

## Usage in Tests

These examples should be used to validate:

1. **Plugin Detection**: Input files trigger correct plugin selection
2. **Format Conversion**: Raw inputs convert to expected Markdown structure
3. **ID Generation**: Each utterance gets unique `clarifai:id` and `^anchor`
4. **Metadata Handling**: File-level metadata is properly formatted
5. **Atomic Writing**: Output files match expected format exactly
6. **Embedding Preparation**: Generated Markdown is suitable for chunking and embedding

## Test Data Characteristics

- **Diversity**: Examples cover different conversation types (technical, casual, formal)
- **Edge Cases**: Include empty messages, special characters, multi-line content
- **Metadata Variety**: Different participant counts, timestamps, and plugin metadata
- **Realistic Content**: Based on actual conversation patterns from various platforms
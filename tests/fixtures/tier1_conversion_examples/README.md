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
│   ├── chatgpt_export.json     # ChatGPT JSON export format
│   ├── slack_export.csv        # Slack CSV export format  
│   ├── plain_text_chat.txt     # Plain text conversation
│   └── unrecognized_format.xyz # Mock unrecognized format
└── expected_outputs/            # Golden standard Tier 1 Markdown files
    ├── chatgpt_export.md
    ├── slack_export.md
    ├── plain_text_chat.md
    └── unrecognized_format.md
```

## Format Specifications

### Input Files
- **JSON**: ChatGPT-style exports with speaker/message structure
- **CSV**: Slack-style exports with timestamp, user, message columns
- **TXT**: Plain text conversations with speaker prefixes
- **XYZ**: Mock unrecognized format for fallback LLM testing

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
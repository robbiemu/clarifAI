# Vault Sync Test Fixtures

This directory contains test fixtures for validating the vault synchronization functionality.

## Files

- `tier1_conversation.md`: Example Tier 1 conversation with inline clarifai:id blocks
- `tier3_concept_page.md`: Example Tier 3 concept page with file-level clarifai:id
- `mixed_content.md`: Example with multiple types of blocks and content
- `no_clarifai_ids.md`: Example file without any clarifai:id markers

These fixtures are used to test:
- Block extraction from various markdown formats
- Hash calculation consistency
- Sync job processing logic
- Error handling for malformed content
# Vault Watcher Service

File monitoring service for detecting changes in Obsidian vaults and triggering processing.

## Overview

The vault-watcher service monitors an Obsidian vault for file changes and emits notifications to the ClarifAI processing pipeline. It detects when markdown files are created, modified, or deleted and sends appropriate messages to trigger claim extraction and analysis.

## Features

- **Real-time Monitoring**: Uses file system watchers to detect changes immediately
- **Intelligent Filtering**: Only processes relevant markdown files and ignores temporary files
- **Dirty Block Tracking**: Identifies specific content blocks that need reprocessing
- **Message Queue Integration**: Sends notifications via RabbitMQ for async processing
- **Robust Error Handling**: Handles file system events gracefully with retry logic

## Architecture

### Components

- **File System Watcher**: Monitors vault directory for changes using `watchdog`
- **Event Filter**: Filters relevant events and extracts block-level changes
- **Message Publisher**: Sends change notifications to the message queue
- **Configuration Manager**: Handles vault paths and monitoring settings

### Key Modules

```
vault_watcher/
├── __init__.py
├── main.py                 # Service entry point
├── watcher/                # File monitoring logic
│   ├── __init__.py
│   ├── file_watcher.py     # File system event handling
│   ├── event_filter.py     # Event filtering and processing
│   └── change_detector.py  # Block-level change detection
├── messaging/              # Message queue integration
│   ├── __init__.py
│   └── publisher.py        # RabbitMQ message publishing
└── config/                 # Configuration management
    ├── __init__.py
    └── settings.py         # Service configuration
```

## Configuration

Environment variables for service configuration:

- `VAULT_PATH`: Path to the Obsidian vault to monitor
- `RABBITMQ_HOST`: RabbitMQ broker hostname
- `RABBITMQ_PORT`: RabbitMQ broker port (default: 5672)
- `RABBITMQ_USER`: RabbitMQ username
- `RABBITMQ_PASSWORD`: RabbitMQ password
- `WATCH_PATTERNS`: File patterns to monitor (default: *.md)
- `IGNORE_PATTERNS`: Patterns to ignore (default: .*, #*)

## Dependencies

### Core Dependencies
- **File Monitoring**: watchdog
- **Message Queue**: pika (RabbitMQ client)
- **Configuration**: pydantic, python-dotenv
- **Shared Package**: clarifai-shared (local)

### Development Dependencies
- **Testing**: pytest, pytest-asyncio, pytest-mock

## Usage

### As a Service
```bash
cd services/vault-watcher
poetry install
poetry run python -m vault_watcher
```

### Development
```bash
# Run tests
poetry run pytest

# Type checking
poetry run mypy vault_watcher

# Linting
poetry run ruff check vault_watcher
```

## Event Types

The service publishes different message types:

### File Events
- `file.created`: New markdown file detected
- `file.modified`: Existing file content changed
- `file.deleted`: File removed from vault

### Block Events
- `block.dirty`: Specific content block needs reprocessing
- `block.updated`: Block content has been modified

## Message Format

Messages sent to the queue include:

```json
{
  "event_type": "file.modified",
  "file_path": "/vault/notes/document.md",
  "timestamp": "2024-01-01T12:00:00Z",
  "block_ids": ["blk_123", "blk_456"],
  "metadata": {
    "file_size": 1024,
    "last_modified": "2024-01-01T11:59:00Z"
  }
}
```

## Integration

Integrates with other ClarifAI services:
- **clarifai-core**: Sends file change notifications for processing
- **scheduler**: Coordinates with batch processing jobs
- **shared**: Uses common messaging and configuration utilities

## Monitoring

The service provides:
- Health check endpoints
- File monitoring statistics
- Error logging and alerting
- Performance metrics
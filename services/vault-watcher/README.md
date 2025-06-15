# ClarifAI Vault Watcher Service

The Vault Watcher service monitors the vault directory for changes in Markdown files and detects dirty blocks based on `clarifai:id` and `ver=` markers, following the specifications in `docs/arch/on-graph_vault_synchronization.md`.

## Features

- **File Monitoring**: Uses `watchdog` to monitor `.md` files in vault directories (Tier 1, 2, 3)
- **Block Detection**: Parses Markdown files to identify `clarifai:id` and `ver=` markers
- **Block Diffing**: Compares content hash and version to detect dirty blocks
- **Batching**: Groups file change events to handle bulk operations efficiently
- **RabbitMQ Integration**: Publishes dirty block notifications to `clarifai_dirty_blocks` queue
- **Structured Logging**: Follows project logging guidelines with service identification

## Architecture

### Components

1. **BlockParser** (`block_parser.py`): Extracts ClarifAI blocks from Markdown content
   - Supports both inline blocks and file-level blocks
   - Handles content hashing for change detection
   - Provides block comparison functionality

2. **BatchedFileWatcher** (`file_watcher.py`): Monitors file system changes
   - Watches for `.md` file changes recursively
   - Batches events to avoid overwhelming the system
   - Filters relevant files and ignores temporary files

3. **DirtyBlockPublisher** (`rabbitmq_publisher.py`): Publishes notifications
   - Connects to RabbitMQ and manages connections
   - Publishes dirty block messages with change metadata
   - Handles connection failures and reconnection

4. **VaultWatcherService** (`main.py`): Main service orchestrator
   - Coordinates all components
   - Manages service lifecycle
   - Handles initial vault scanning

### Block Types

- **Inline Blocks**: Individual sentences/paragraphs marked with `<!-- clarifai:id=xxx ver=N -->`
- **File-Level Blocks**: Entire files marked with comment at the end

### Message Format

Published messages include:
```json
{
  "clarifai_id": "clm_abc123",
  "file_path": "/vault/file.md",
  "change_type": "modified|added|deleted",
  "timestamp": 1234567890000,
  "version": 2,
  "block_type": "inline|file"
}
```

## Configuration

The service uses the central `clarifai.config.yaml` for configuration:
- `vault_path`: Path to the vault directory to monitor
- `rabbitmq_host`: RabbitMQ server host
- `rabbitmq_port`: RabbitMQ server port (default: 5672)

## Usage

Run the service as a standalone process:
```bash
python -m clarifai_vault_watcher.main
```

Or use Docker:
```bash
docker-compose up vault-watcher
```

## Testing

Run tests with:
```bash
pytest tests/
```

The test suite includes:
- Block parser functionality tests
- File watcher integration tests  
- RabbitMQ publisher tests
- Service lifecycle tests

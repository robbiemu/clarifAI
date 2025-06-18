# Block Syncing Loop Implementation

This document describes the implementation of the reactive block synchronization loop for Sprint 4, which processes dirty block notifications from the vault-watcher service.

## Overview

The block syncing loop is implemented in `services/aclarai-core/aclarai_core/dirty_block_consumer.py` as the `DirtyBlockConsumer` class. This service:

1. Consumes RabbitMQ messages from the `aclarai_dirty_blocks` queue
2. Processes individual dirty block notifications
3. Implements proper version checking with optimistic locking
4. Updates graph nodes with incremented versions
5. Marks updated nodes for reprocessing

## Architecture

### Message Flow

1. **vault-watcher** detects file changes and publishes dirty block messages to RabbitMQ
2. **aclarai-core** consumes these messages via `DirtyBlockConsumer`
3. For each message, the consumer:
   - Reads the current block content from the vault file
   - Compares version with the graph version  
   - Updates the graph node if appropriate
   - Marks the node with `needs_reprocessing: true`

### Version Checking Logic

The implementation follows the optimistic locking strategy from `docs/arch/on-graph_vault_synchronization.md`:

- **If `vault_ver == graph_ver`**: Clean update, increment graph version
- **If `vault_ver > graph_ver`**: Proceed with update (vault is more recent)  
- **If `vault_ver < graph_ver`**: **Conflict detected** - skip update and log warning

### Version Incrementing

When updating a block in the graph:
- The graph version is incremented (`graph_ver + 1`)
- This differs from using the vault version directly
- Ensures proper version sequencing in the graph

## Key Components

### DirtyBlockConsumer

Main class that handles:
- RabbitMQ connection and message consumption
- Block parsing and version checking
- Graph updates with proper error handling

### Message Processing

Each RabbitMQ message contains:
```json
{
  "aclarai_id": "clm_abc123",
  "file_path": "tier1/conversation.md", 
  "change_type": "modified",
  "timestamp": 1234567890,
  "version": 2,
  "block_type": "inline"
}
```

### Block Reading

For each dirty block notification:
1. Read the markdown file from the vault
2. Parse all `<!-- aclarai:id=xxx ver=N -->` comments
3. Extract the semantic text for the specific block
4. Calculate content hash for change detection

## Configuration

The consumer uses the shared configuration system:
- RabbitMQ connection details from `config.rabbitmq_host`
- Vault path from `config.vault_path`
- Neo4j connection via `Neo4jGraphManager`

## Error Handling

- **Message parsing errors**: Bad JSON messages are acknowledged and removed
- **File read errors**: Messages are requeued for retry
- **Graph update errors**: Messages are requeued with exponential backoff
- **Version conflicts**: Logged as warnings but don't fail the message

## Integration

### With vault-watcher

- Consumes messages published by `DirtyBlockPublisher`
- Uses the same queue name: `aclarai_dirty_blocks`
- Handles message format from vault-watcher

### With Neo4j Graph

- Updates `:Block` nodes with new text and hash
- Increments version numbers properly
- Sets `needs_reprocessing: true` for downstream processing

### With Scheduler

- Independent from the periodic `VaultSyncJob`
- Handles real-time updates while scheduler handles bulk sync
- Both services can run concurrently

## Testing

Comprehensive test suite covers:
- Block extraction from markdown
- Version checking logic  
- Conflict detection
- Graph update operations
- Message processing edge cases

## Deployment

The consumer runs as part of the `aclarai-core` service:
1. Start the service via `docker-compose up aclarai-core`
2. Consumer automatically begins processing messages
3. Graceful shutdown on SIGINT/SIGTERM

## Differences from Periodic Sync

| Aspect | Reactive Sync Loop | Periodic Vault Sync |
|--------|-------------------|---------------------|
| Trigger | RabbitMQ messages | Scheduled cron job |
| Scope | Individual blocks | All vault files |
| Version Logic | Increment graph version | Use vault version |
| Performance | Real-time updates | Batch processing |
| Error Handling | Message requeue | Job retry |

## Future Enhancements

- Support for deleted block handling
- Batch processing of multiple messages
- Dead letter queue for failed messages
- Metrics and monitoring integration
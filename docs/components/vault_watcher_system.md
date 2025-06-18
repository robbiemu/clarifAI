# Vault Watcher System

The vault watcher system monitors Markdown files in the vault and detects dirty blocks for real-time synchronization with the Neo4j knowledge graph.

## Overview

The vault watcher service provides real-time monitoring infrastructure for the aclarai vault directory, enabling immediate detection of content changes for downstream processing by the synchronization system.

Key responsibilities:

- **File System Monitoring**: Watches `.md` files across vault tiers for changes
- **Block Change Detection**: Identifies dirty blocks using `aclarai:id` and version markers
- **Event Batching**: Groups file changes to handle bulk operations efficiently  
- **Queue Publishing**: Emits dirty block notifications via RabbitMQ for async processing

## Architecture

The vault watcher system follows aclarai architectural patterns:

- **Structured Logging**: Adheres to `docs/arch/idea-logging.md` with service context and contextual IDs
- **Error Handling**: Implements `docs/arch/on-error-handling-and-resilience.md` patterns with retry logic
- **Graph Synchronization**: Supports `docs/arch/on-graph_vault_synchronization.md` dirty detection workflow
- **Configuration Management**: All parameters sourced from `settings/aclarai.config.yaml`

## Core Components

### VaultWatcherService

Main service orchestrator (`aclarai_vault_watcher.main`) that:

- Coordinates file watching, block parsing, and message publishing
- Performs initial vault scan to establish baseline state
- Manages service lifecycle with proper cleanup
- Handles configuration from central config file

### BlockParser

Markdown block extraction engine (`aclarai_vault_watcher.block_parser`) that:

- **Inline Block Detection**: Finds `<!-- aclarai:id=xxx ver=N -->` markers in content
- **File-Level Block Detection**: Identifies entire-file markers at document end
- **Content Hashing**: Uses SHA-256 with whitespace normalization for change detection
- **Block Comparison**: Provides dirty detection by comparing content hashes and versions

### BatchedFileWatcher

File system monitoring with intelligent batching (`aclarai_vault_watcher.file_watcher`):

- **Efficient Monitoring**: Uses `watchdog` library for cross-platform file system events
- **Batching Logic**: Groups events within configurable time windows (default 2s)
- **Bulk Operation Handling**: Processes up to 50 events per batch to handle git pulls
- **File Filtering**: Monitors `.md` files while ignoring temporary/hidden files

### DirtyBlockPublisher  

RabbitMQ integration for async messaging (`aclarai_vault_watcher.rabbitmq_publisher`):

- **Queue Publishing**: Sends dirty block notifications to `aclarai_dirty_blocks` queue
- **Connection Management**: Handles RabbitMQ connection failures and reconnection
- **Message Format**: Structured JSON with change metadata and contextual information

## Block Detection Logic

The vault watcher supports both granular and file-level content tracking as specified in `docs/arch/on-graph_vault_synchronization.md`:

### Inline Blocks

Individual content units marked with HTML comments:

```markdown
Some claim or summary text. <!-- aclarai:id=clm_abc123 ver=2 -->
^clm_abc123
```

### File-Level Blocks

Entire documents tracked as single units:

```markdown
## Document Content

Content body...

<!-- aclarai:id=file_concepts_summary ver=1 -->
```

### Change Detection

Content changes are detected by:

1. **Hash Comparison**: SHA-256 of normalized text content (whitespace-agnostic)
2. **Version Tracking**: Version increments indicate semantic changes
3. **Block Lifecycle**: Tracks added, modified, and deleted blocks

## Message Format

Published dirty block notifications include complete change context:

```json
{
  "aclarai_id": "clm_abc123",
  "file_path": "/vault/concepts/example.md", 
  "change_type": "modified",
  "timestamp": 1734294000000,
  "version": 2,
  "block_type": "inline"
}
```

Change types: `added`, `modified`, `deleted`
Block types: `inline`, `file_level`

## Configuration

Vault watcher behavior is configured via `settings/aclarai.config.yaml`:

```yaml
vault_watcher:
  batch_interval: 2.0      # Seconds to batch file events
  max_batch_size: 50       # Maximum events per batch
  
  rabbitmq:
    queue_name: "aclarai_dirty_blocks"
    exchange: ""           # Use default exchange
    routing_key: "aclarai_dirty_blocks"
    
  file_patterns:
    include: ["*.md"]      # Only monitor markdown files
    exclude: [".*", "*.tmp", "*~"]  # Ignore temp/hidden files
```

Database connections use the standard `databases.rabbitmq` configuration section.

## Integration Points

The vault watcher integrates with the broader aclarai ecosystem:

- **Upstream**: Monitors vault files modified by users, import system, or agent generation
- **Downstream**: Feeds the scheduler's `vault_sync` job for graph synchronization
- **Coordination**: Works with file conflict detection patterns from `docs/arch/on-filehandle_conflicts.md`

## Performance Characteristics

- **Event Batching**: 2-second windows prevent overwhelming downstream systems
- **Efficient Parsing**: Incremental block detection minimizes processing overhead
- **Async Publishing**: Non-blocking RabbitMQ integration maintains responsiveness
- **Memory Efficiency**: Stateless design with minimal memory footprint for large vaults
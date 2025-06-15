# Scheduler System

The scheduler system provides periodic job execution infrastructure for the ClarifAI ecosystem using APScheduler (Advanced Python Scheduler).

## Overview

The scheduler service runs background tasks on configurable cron schedules, including:

- **Vault Synchronization**: Maintains consistency between Markdown files and the Neo4j knowledge graph
- **Concept Hygiene**: Deduplication and refinement operations (future enhancement)
- **Embedding Refresh**: Updates embeddings for changed content (future enhancement)
- **Reprocessing Tasks**: Handles content marked for reprocessing (future enhancement)

## Architecture

The scheduler system follows ClarifAI architectural patterns:

- **Structured Logging**: Adheres to `docs/arch/idea-logging.md` with service context and job IDs
- **Error Handling**: Implements `docs/arch/on-error-handling-and-resilience.md` patterns
- **Neo4j Integration**: Uses `docs/arch/on-neo4j_interaction.md` direct Cypher approach
- **Configuration Management**: All parameters sourced from `settings/clarifai.config.yaml`

## Core Components

### SchedulerService

Main service class (`clarifai_scheduler.main`) that:

- Initializes APScheduler with thread pool executors
- Registers jobs from configuration
- Handles graceful shutdown and signal management
- Provides centralized logging and error handling

### VaultSyncJob

Vault-to-graph synchronization implementation (`clarifai_scheduler.vault_sync`) following `docs/arch/on-graph_vault_synchronization.md`:

- **Block Extraction**: Parses Markdown files for `clarifai:id` blocks
- **Change Detection**: Uses SHA-256 hashes of semantic text content
- **Graph Synchronization**: Creates/updates Block nodes with version tracking
- **Statistics Tracking**: Provides detailed metrics on sync operations

## Configuration

Jobs are configured via `settings/clarifai.config.yaml`:

```yaml
scheduler:
  jobs:
    vault_sync:
      enabled: true
      cron: "*/30 * * * *"
      description: "Sync vault files with knowledge graph"
```

## Environment Controls

- `AUTOMATION_PAUSE`: Set to "true" to pause all scheduled jobs
- Service-specific environment variables can override job configurations

## Synchronization Logic

The vault sync job implements the specification from `docs/arch/on-graph_vault_synchronization.md`:

### Block Types Supported

- **Inline blocks**: Individual sentences/claims with `<!-- clarifai:id=blk_abc123 ver=1 -->`
- **File-level blocks**: Agent-generated content with file-scope IDs

### Change Detection

- Calculates SHA-256 hashes of visible content (excluding metadata comments)
- Compares with stored hashes in Neo4j Block nodes
- Increments version numbers and sets `needs_reprocessing` flags for changes

### Multi-tier Processing

- **Tier 1**: Always processed (required content)
- **Tier 2/3**: Processed when `clarifai:id` markers are present
- Configurable file inclusion patterns

## Logging Format

All operations use structured logging with required context:

```json
{
  "level": "INFO",
  "service": "clarifai-scheduler",
  "filename.function_name": "vault_sync.run_sync",
  "job_id": "vault_sync_1734264000",
  "blocks_processed": 42,
  "blocks_updated": 3,
  "duration": 2.1
}
```

## Error Handling

The system implements resilient patterns:

- **Retry Logic**: Exponential backoff for transient Neo4j connection errors
- **Graceful Degradation**: Jobs continue processing other files if individual files fail
- **Atomic Operations**: Database updates use transactions to prevent partial state
- **Signal Handling**: Graceful shutdown on SIGINT/SIGTERM

## Performance Considerations

- **Thread Pool Execution**: Jobs run in isolated threads to prevent blocking
- **Batch Processing**: Neo4j operations use efficient batch patterns
- **Memory Management**: Large vaults processed incrementally
- **Connection Pooling**: Neo4j driver handles connection lifecycle

## Monitoring and Observability

Each job execution provides:

- **Start/completion timestamps**
- **Processing statistics** (files scanned, blocks updated, errors)
- **Performance metrics** (execution duration, throughput)
- **Error details** with stack traces for debugging

## Dependencies

The scheduler system builds on:

- **APScheduler**: Job scheduling and execution framework
- **clarifai_shared**: Configuration, logging, and Neo4j components
- **Neo4j Python Driver**: Database operations
- **Standard Library**: Signal handling, hashing, file operations

## Future Enhancements

Planned extensions include:

- **Concept Embedding Refresh**: Periodic vector store updates
- **Hygiene Jobs**: Automated cleanup and deduplication
- **Advanced Scheduling**: Dependency-based job execution
- **Performance Optimization**: Incremental sync for large vaults
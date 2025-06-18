# Concept Embedding Refresh System

This document describes the implementation of the concept embedding refresh system in aclarai, which automatically updates embeddings for Tier 3 concept files on a scheduled basis.

## Overview

The concept embedding refresh job runs nightly (configurable via cron) to ensure that all concept embeddings in the vector store accurately reflect the current content of their corresponding Tier 3 Markdown files in the vault.

## Architecture

### Components

1. **ConceptEmbeddingRefreshJob** (`services/scheduler/aclarai_scheduler/concept_refresh.py`)
   - Main job class that orchestrates the refresh process
   - Integrates with the APScheduler system
   - Provides comprehensive logging and error handling

2. **Scheduler Integration** (`services/scheduler/aclarai_scheduler/main.py`)
   - Registers the concept refresh job with APScheduler
   - Handles job execution and reporting
   - Respects environment variable overrides

3. **Configuration** (`shared/aclarai_shared/aclarai.config.default.yaml`)
   - Job scheduling settings (cron: "0 3 * * *" - 3 AM daily)
   - Enable/disable toggle
   - Vector store configuration for concepts collection

## Process Flow

The refresh job follows this process for each concept file:

1. **Discovery**: Scan `vault/concepts/*.md` for all concept files
2. **Content Extraction**: Read file content and extract semantic text by:
   - Removing metadata lines (`<!-- aclarai:...`)
   - Removing anchor references (`^concept_...`)
3. **Change Detection**: 
   - Compute SHA256 hash of semantic text
   - Compare with stored `embedding_hash` in Neo4j `:Concept` node
4. **Conditional Update**: If hashes differ or stored hash is null:
   - Generate new embedding using configured embedding model
   - Update vector store with new embedding (upsert operation)
   - Update Neo4j metadata (`embedding_hash`, `last_updated`)

## Configuration

### Job Settings

```yaml
scheduler:
  jobs:
    concept_embedding_refresh:
      enabled: true
      cron: "0 3 * * *"  # 3 AM daily
      description: "Refresh concept embeddings from Tier 3 pages"
```

### Environment Overrides

- `CONCEPT_EMBEDDING_REFRESH_ENABLED`: Override job enabled state
- `CONCEPT_EMBEDDING_REFRESH_CRON`: Override cron schedule

### Vector Store

The system uses the `concepts` collection configured in:

```yaml
concepts:
  canonical:
    collection_name: "concepts"
    similarity_threshold: 0.95
```

## Logging

The system provides structured logging with the following context:

- `service`: "aclarai-scheduler"
- `filename.function_name`: Specific function being executed
- `concept_name`: Name of concept being processed
- `concept_file`: Path to concept file
- Job statistics (processed, updated, skipped, errors)

### Log Examples

```json
{
  "level": "INFO",
  "service": "aclarai-scheduler", 
  "filename.function_name": "concept_refresh.run_job",
  "concepts_processed": 15,
  "concepts_updated": 3,
  "concepts_skipped": 12,
  "errors": 0,
  "duration": 2.1
}
```

## Error Handling

The system is designed to be resilient:

- **File-level isolation**: Errors processing one concept don't affect others
- **Graceful degradation**: Missing concepts directory or Neo4j connectivity issues are logged but don't crash the job
- **Retry logic**: Built into underlying Neo4j and embedding service integrations
- **Hash fallback**: Returns null hash on Neo4j query errors to force embedding update

## Monitoring

Job execution includes comprehensive statistics:

- `concepts_processed`: Total files examined
- `concepts_updated`: Files with changed embeddings
- `concepts_skipped`: Files with no changes
- `errors`: Number of processing errors
- `error_details`: Specific error messages
- `duration`: Total execution time
- `success`: Overall job success status

## Dependencies

The system depends on:

1. **Neo4j**: For storing concept metadata and embedding hashes
2. **Embedding Service**: Configured embedding model for generating vectors
3. **Vector Store**: Concepts collection for storing embeddings
4. **Concept Infrastructure**: `:Concept` nodes from Sprint 5 tasks

## Usage

### Manual Execution

For testing purposes, the job can be executed manually:

```python
from aclarai_scheduler.concept_refresh import ConceptEmbeddingRefreshJob
from aclarai_shared import load_config

config = load_config()
job = ConceptEmbeddingRefreshJob(config)
result = job.run_job()
print(result)
```

### Scheduled Execution

The job runs automatically when the scheduler service is started and the job is enabled in configuration.

## Testing

The system includes comprehensive tests covering:

- Semantic text extraction with and without metadata
- Hash computation consistency
- Change detection logic
- File processing (both changed and unchanged files)
- Error scenarios and edge cases
- Integration with scheduler system

Run tests with:

```bash
uv run python -m pytest tests/test_concept_refresh.py -v
```

## Future Enhancements

Potential improvements for future sprints:

1. **Batch Processing**: Process multiple concepts in embedding batches for efficiency
2. **Incremental Timestamps**: Use file modification times as an additional change indicator
3. **Drift Analysis**: Track semantic drift patterns over time
4. **Performance Metrics**: Detailed timing for each processing stage
5. **Concept Validation**: Verify concept files match expected format before processing

## Related Documentation

- [Concept Embedding Architecture](../arch/on-refreshing_concept_embeddings.md)
- [Scheduler Setup Guide](../guides/scheduler_setup_guide.md)
- [Vector Stores Guide](../arch/on-vector_stores.md)
- [Concept Detection System](./concept_detection_system.md)
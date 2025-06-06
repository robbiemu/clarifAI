# Scheduler Service

Task scheduling service for managing periodic jobs and background processing in the ClarifAI system.

## Overview

The scheduler service orchestrates automated tasks within the ClarifAI ecosystem. It manages nightly jobs, periodic maintenance, batch processing, and ensures system hygiene through automated workflows.

## Features

- **Cron-like Scheduling**: Flexible scheduling with cron expressions
- **Job Management**: Create, update, and monitor scheduled jobs
- **Batch Processing**: Handle large-scale processing operations
- **System Maintenance**: Automated cleanup and optimization tasks
- **Resilient Execution**: Retry logic and error handling for failed jobs
- **Integration**: Seamless coordination with other ClarifAI services

## Architecture

### Components

- **Job Scheduler**: Core scheduling engine using APScheduler
- **Task Queue**: Celery-based distributed task processing
- **Job Registry**: Manages job definitions and metadata
- **Execution Monitor**: Tracks job status and performance
- **Message Coordinator**: Interfaces with other services via RabbitMQ

### Key Modules

```
scheduler/
├── __init__.py
├── main.py                 # Service entry point
├── jobs/                   # Job definitions and handlers
│   ├── __init__.py
│   ├── concept_hygiene.py  # Concept drift detection and merging
│   ├── vault_sync.py       # Vault synchronization tasks
│   ├── batch_processing.py # Large-scale processing jobs
│   └── maintenance.py      # System cleanup and optimization
├── scheduler/              # Core scheduling logic
│   ├── __init__.py
│   ├── job_scheduler.py    # APScheduler integration
│   ├── task_queue.py       # Celery task queue
│   └── job_registry.py     # Job management
├── monitoring/             # Job monitoring and status
│   ├── __init__.py
│   ├── job_monitor.py      # Execution tracking
│   └── metrics.py          # Performance metrics
└── config/                 # Configuration management
    ├── __init__.py
    └── settings.py         # Service configuration
```

## Scheduled Jobs

### Nightly Jobs

#### Concept Hygiene (2:00 AM)
- Refresh embeddings from Tier 3 files
- Detect near-duplicate concepts
- Merge concept drift automatically
- Clean up orphaned graph nodes

#### Vault Synchronization (3:00 AM)
- Scan for missed file changes
- Reconcile graph-vault inconsistencies
- Update document metadata
- Validate reference integrity

#### System Maintenance (4:00 AM)
- Database optimization and cleanup
- Log rotation and archival
- Performance metric collection
- Health check validation

### Periodic Jobs

#### Batch Reprocessing (Weekly)
- Reprocess documents with updated models
- Regenerate embeddings with improved algorithms
- Update concept relationships
- Quality assessment and validation

## Configuration

Environment variables for service configuration:

- `SCHEDULER_TIMEZONE`: Timezone for job scheduling (default: UTC)
- `RABBITMQ_HOST`: RabbitMQ broker hostname
- `CELERY_BROKER_URL`: Celery broker URL
- `CELERY_RESULT_BACKEND`: Result backend for task status
- `JOB_TIMEOUT`: Default job timeout in seconds
- `MAX_RETRIES`: Maximum retry attempts for failed jobs
- `ENABLE_MONITORING`: Enable job monitoring (default: true)

## Dependencies

### Core Dependencies
- **Scheduling**: apscheduler, celery, croniter
- **Message Queue**: pika (RabbitMQ client)
- **Configuration**: pydantic, python-dotenv
- **Shared Package**: clarifai-shared (local)

### Development Dependencies
- **Testing**: pytest, pytest-asyncio, pytest-mock

## Usage

### As a Service
```bash
cd services/scheduler
poetry install
poetry run python -m scheduler
```

### Development
```bash
# Run tests
poetry run pytest

# Type checking
poetry run mypy scheduler

# Linting
poetry run ruff check scheduler
```

### Manual Job Execution
```python
from scheduler.jobs import concept_hygiene

# Run concept hygiene job manually
concept_hygiene.run_concept_hygiene()

# Schedule a one-time batch processing job
scheduler.schedule_batch_processing(
    documents=["doc1.md", "doc2.md"],
    priority="high"
)
```

## Job Types

### Recurring Jobs
- **Concept Hygiene**: Daily concept maintenance
- **Vault Sync**: Daily vault synchronization  
- **System Maintenance**: Daily system cleanup
- **Batch Reprocessing**: Weekly bulk processing

### On-Demand Jobs
- **Manual Reprocessing**: User-triggered document reprocessing
- **Emergency Sync**: Immediate vault synchronization
- **Data Export**: Generate system reports and exports
- **Diagnostics**: System health and performance checks

## Monitoring

The service provides comprehensive monitoring:

### Job Status Tracking
- Execution history and logs
- Success/failure rates
- Performance metrics
- Resource utilization

### Alerting
- Failed job notifications
- Performance threshold alerts
- System health warnings
- Resource exhaustion alerts

### Metrics
- Job execution times
- Queue depth and throughput
- Error rates and patterns
- System resource usage

## Integration

Integrates with other ClarifAI services:
- **clarifai-core**: Triggers processing jobs and receives status updates
- **vault-watcher**: Coordinates file monitoring with batch processing
- **clarifai-ui**: Provides job control and monitoring interface
- **shared**: Uses common messaging, configuration, and data models

## Error Handling

Robust error handling includes:
- Automatic retry with exponential backoff
- Dead letter queues for failed jobs
- Circuit breaker patterns for external dependencies
- Comprehensive logging and alerting
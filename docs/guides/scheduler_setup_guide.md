# Scheduler Job Setup Guide

This guide explains how to set up and configure periodic jobs using aclarai's scheduler service.

## Overview

The aclarai scheduler uses APScheduler (Advanced Python Scheduler) to run periodic background tasks. Jobs are configured through the central configuration file and can be enabled/disabled and customized as needed.

## Basic Job Configuration

### Configuration File Structure

Jobs are defined in `settings/aclarai.config.yaml` under the `scheduler.jobs` section:

```yaml
scheduler:
  jobs:
    job_name:
      enabled: true
      cron: "*/30 * * * *"
      description: "Job description"
      # Additional job-specific parameters
```

### Cron Schedule Format

The scheduler uses standard cron format for scheduling:

- `* * * * *` - Minute, Hour, Day of Month, Month, Day of Week
- Examples:
  - `"*/30 * * * *"` - Every 30 minutes
  - `"0 */6 * * *"` - Every 6 hours
  - `"0 3 * * *"` - Daily at 3:00 AM
  - `"0 0 * * 0"` - Weekly on Sunday at midnight

## Built-in Jobs

### Vault Sync Job

Synchronizes Markdown files in the vault with the Neo4j knowledge graph.

```yaml
scheduler:
  jobs:
    vault_sync:
      enabled: true
      cron: "*/30 * * * *"  # Every 30 minutes
      description: "Sync vault files with knowledge graph"
```

**What it does:**
- Scans Tier 1, 2, and 3 Markdown files for `aclarai:id` blocks
- Calculates content hashes to detect changes
- Updates Neo4j nodes with new content and version numbers
- Marks changed blocks for reprocessing

**Configuration options:**
- `enabled`: Enable/disable the job (default: true)
- `cron`: Schedule using cron format
- `description`: Human-readable description

## Environment Controls

### Global Automation Pause

Set the `AUTOMATION_PAUSE` environment variable to temporarily disable all scheduled jobs:

```bash
export AUTOMATION_PAUSE=true
```

This is useful for maintenance, debugging, or when running manual operations.

### Individual Job Controls

Individual jobs can be disabled by setting their `enabled` flag to `false` in the configuration:

```yaml
scheduler:
  jobs:
    vault_sync:
      enabled: false  # Disables this specific job
      cron: "*/30 * * * *"
      description: "Sync vault files with knowledge graph"
```

## Adding Custom Jobs

### Step 1: Implement Job Class

Create a new job class following the pattern used by `VaultSyncJob`:

```python
# services/scheduler/aclarai_scheduler/my_custom_job.py

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class MyCustomJob:
    """Custom job implementation."""
    
    def __init__(self, config=None):
        """Initialize job with configuration."""
        self.config = config or load_config(validate=True)
    
    def run_job(self) -> Dict[str, Any]:
        """
        Execute the job logic.
        
        Returns:
            Dictionary with job results and statistics
        """
        logger.info("Starting custom job")
        
        try:
            # Your job logic here
            result = self._do_work()
            
            logger.info("Custom job completed successfully")
            return {
                "success": True,
                "items_processed": result["count"],
                "duration": result["duration"]
            }
            
        except Exception as e:
            logger.error(f"Custom job failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _do_work(self):
        """Implement your job logic here."""
        # Custom implementation
        pass
```

### Step 2: Register Job in Main Service

Add your job to the scheduler service in `services/scheduler/aclarai_scheduler/main.py`:

```python
from .my_custom_job import MyCustomJob

class SchedulerService:
    def _register_jobs(self):
        """Register all available jobs."""
        # Existing jobs
        if self.config.scheduler.jobs.get("vault_sync", {}).get("enabled", True):
            self._register_vault_sync_job()
        
        # Add your custom job
        if self.config.scheduler.jobs.get("my_custom_job", {}).get("enabled", False):
            self._register_my_custom_job()
    
    def _register_my_custom_job(self):
        """Register the custom job."""
        job_config = self.config.scheduler.jobs.get("my_custom_job", {})
        cron_schedule = job_config.get("cron", "0 2 * * *")  # Default: 2 AM daily
        
        job = MyCustomJob(self.config)
        
        self.scheduler.add_job(
            func=self._run_job_with_logging,
            args=("my_custom_job", job.run_job),
            trigger="cron",
            **self._parse_cron(cron_schedule),
            id="my_custom_job",
            name="My Custom Job",
            misfire_grace_time=300,
            coalesce=True,
            max_instances=1
        )
```

### Step 3: Add Configuration

Add your job configuration to `settings/aclarai.config.yaml`:

```yaml
scheduler:
  jobs:
    my_custom_job:
      enabled: false  # Start disabled for safety
      cron: "0 2 * * *"  # Daily at 2 AM
      description: "My custom periodic job"
      # Add any job-specific configuration here
      custom_param: "value"
```

## Monitoring and Logging

### Job Execution Logging

The scheduler automatically logs job execution with structured format:

```json
{
  "level": "INFO",
  "service": "aclarai-scheduler",
  "filename.function_name": "main._run_job_with_logging",
  "job_id": "vault_sync_1734264000",
  "job_name": "vault_sync",
  "duration": 2.1,
  "success": true
}
```

### Job Statistics

Jobs should return statistics dictionaries for monitoring:

```python
def run_job(self) -> Dict[str, Any]:
    return {
        "success": True,
        "items_processed": 42,
        "items_updated": 3,
        "errors": 0,
        "duration": 2.1
    }
```

## Running the Scheduler

### Development

```bash
cd services/scheduler
python -m aclarai_scheduler.main
```

### Docker

```bash
docker build -t aclarai-scheduler .
docker run aclarai-scheduler
```

### Docker Compose

The scheduler is included in the main docker-compose.yml:

```bash
docker compose up aclarai-scheduler
```

## Troubleshooting

### Common Issues

1. **Jobs not starting**: Check that `enabled: true` in configuration
2. **Database connection errors**: Verify database credentials in `.env`
3. **Import errors**: Ensure all dependencies are installed
4. **Permission errors**: Check file system permissions for vault access

### Debugging

Enable debug logging by setting `LOG_LEVEL=DEBUG` in your environment:

```bash
export LOG_LEVEL=DEBUG
python -m aclarai_scheduler.main
```

### Manual Job Execution

For testing, you can run jobs manually:

```python
from aclarai_scheduler.vault_sync import VaultSyncJob
from aclarai_shared import load_config

config = load_config()
job = VaultSyncJob(config)
result = job.run_sync()
print(result)
```

## Best Practices

1. **Start with disabled jobs**: Set `enabled: false` for new jobs until tested
2. **Use appropriate schedules**: Don't over-schedule resource-intensive jobs
3. **Handle errors gracefully**: Always catch exceptions and return error status
4. **Log meaningful information**: Include context for debugging
5. **Return statistics**: Provide metrics for monitoring and alerting
6. **Test thoroughly**: Verify job behavior in development before production
7. **Respect automation pause**: Check `AUTOMATION_PAUSE` if implementing custom logic

## Related Documentation

- [Scheduler System Components](../components/scheduler_system.md) - Architecture overview
- [Graph Vault Synchronization](../arch/on-graph_vault_synchronization.md) - Vault sync details
- [Error Handling and Resilience](../arch/on-error-handling-and-resilience.md) - Error handling patterns
- [Structured Logging](../arch/idea-logging.md) - Logging standards
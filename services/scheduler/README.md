# ClarifAI Scheduler

This service provides periodic job execution infrastructure for the ClarifAI ecosystem.

For complete documentation, architecture details, and usage information, see:
**[docs/components/scheduler_system.md](../../docs/components/scheduler_system.md)**

## Quick Start

```bash
cd services/scheduler
python -m clarifai_scheduler.main
```

## Configuration

Configure jobs in `settings/clarifai.config.yaml` under the `scheduler.jobs` section.

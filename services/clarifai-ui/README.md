# ClarifAI UI Service

Gradio-based web interface for ClarifAI configuration, monitoring, and control.

## Overview

The clarifai-ui service provides a user-friendly web interface for interacting with the ClarifAI system. Built with Gradio, it offers configuration panels, monitoring dashboards, and control interfaces for managing the knowledge extraction and organization workflow.

## Features

- **Configuration Panel**: Intuitive interface for system settings and parameters
- **Processing Dashboard**: Real-time monitoring of document processing status
- **Job Management**: Control and monitor scheduled tasks and background jobs  
- **System Diagnostics**: Health checks, performance metrics, and error reporting
- **Data Visualization**: Interactive charts and graphs for system insights
- **Manual Controls**: Trigger processing jobs and manage system operations

## Architecture

### Components

- **Gradio Application**: Main web interface framework
- **FastAPI Backend**: RESTful API for service integration
- **Configuration Manager**: UI for system settings and parameters
- **Monitoring Dashboard**: Real-time status and metrics display
- **Job Controller**: Interface for managing scheduled and manual jobs

### Key Modules

```
clarifai_ui/
├── __init__.py
├── main.py                 # Application entry point
├── app/                    # Gradio application components
│   ├── __init__.py
│   ├── interface.py        # Main Gradio interface
│   ├── config_panel.py     # Configuration interface
│   ├── monitoring.py       # Monitoring dashboard
│   └── job_control.py      # Job management interface
├── api/                    # FastAPI backend
│   ├── __init__.py
│   ├── routes.py           # API route definitions
│   ├── websockets.py       # Real-time updates
│   └── middleware.py       # Request/response middleware
├── components/             # Reusable UI components
│   ├── __init__.py
│   ├── charts.py           # Data visualization components
│   ├── forms.py            # Configuration forms
│   └── tables.py           # Data display tables
└── utils/                  # UI utilities
    ├── __init__.py
    ├── formatting.py       # Data formatting helpers
    └── validation.py       # Input validation
```

## Configuration Interface

### Model & Embedding Settings
- LLM provider selection (OpenAI, Anthropic, etc.)
- Model parameters and API credentials
- Embedding model configuration
- Token limits and cost management

### Processing Parameters
- Similarity thresholds for concept linking
- Chunk sizes and overlap settings
- Batch processing limits
- Quality assessment criteria

### Agent Toggles
- Enable/disable specific processing agents
- Configure agent behavior and parameters
- Set processing priorities and workflows

### Vault Configuration
- Vault path settings and document type detection
- Folder organization preferences
- File filtering and ignore patterns
- Output format configurations

### Automation Control
- Schedule configuration for nightly jobs
- Enable/disable automated processing
- Retry policies and error handling
- Notification settings

## Monitoring Dashboard

### System Status
- Service health indicators
- Database connection status
- Queue depths and processing rates
- Error counts and recent failures

### Processing Metrics
- Documents processed per hour/day
- Claims extracted and concepts identified
- Processing time distributions
- Quality scores and validation results

### Resource Usage
- CPU and memory utilization
- Database storage usage
- Queue message volumes
- Network activity

### Job Status
- Active and scheduled jobs
- Execution history and logs
- Success/failure rates
- Performance trends

## Dependencies

### Core Dependencies
- **UI Framework**: gradio, fastapi, uvicorn
- **Data Visualization**: pandas, plotly
- **API Communication**: httpx, websockets
- **Configuration**: pydantic, python-dotenv
- **Shared Package**: clarifai-shared (local)

### Development Dependencies
- **Testing**: pytest, pytest-asyncio, pytest-mock

## Usage

### As a Service
```bash
cd services/clarifai-ui
poetry install
poetry run python -m clarifai_ui
```

### Development
```bash
# Run tests
poetry run pytest

# Type checking
poetry run mypy clarifai_ui

# Linting
poetry run ruff check clarifai_ui

# Development server with hot reload
poetry run python -m clarifai_ui --dev
```

### Docker Deployment
```bash
# Build image
docker build -t clarifai-ui .

# Run container
docker run -p 7860:7860 clarifai-ui
```

## Interface Sections

### Configuration Panel
- **Model Settings**: Configure AI models and credentials
- **Processing Parameters**: Set thresholds and processing options
- **Vault Settings**: Manage vault paths and document handling
- **Automation**: Configure scheduled jobs and automation

### Monitoring Dashboard
- **System Overview**: High-level system status and metrics
- **Processing Status**: Real-time processing activity
- **Job Monitor**: Scheduled and background job status
- **Performance**: System performance metrics and trends

### Job Control
- **Manual Jobs**: Trigger one-time processing tasks
- **Scheduled Jobs**: View and manage recurring jobs
- **Batch Processing**: Initiate large-scale processing operations
- **System Actions**: Restart services, clear caches, etc.

### Diagnostics
- **Health Checks**: System component health status
- **Error Logs**: Recent errors and troubleshooting information
- **Performance Analysis**: Detailed performance metrics
- **Configuration Validation**: Verify system configuration

## API Integration

The UI service provides RESTful APIs for:
- Configuration management
- Status monitoring
- Job control
- System diagnostics

### WebSocket Support
Real-time updates via WebSocket connections:
- Live processing status
- Job execution updates
- System alerts and notifications
- Performance metric streams

## Security

- **Authentication**: Optional user authentication
- **Authorization**: Role-based access control
- **CSRF Protection**: Cross-site request forgery protection
- **Input Validation**: Comprehensive input sanitization

## Integration

Integrates with other ClarifAI services:
- **clarifai-core**: Monitor processing status and trigger jobs
- **vault-watcher**: View file monitoring status and statistics
- **scheduler**: Manage scheduled jobs and view execution history
- **shared**: Use common configuration and data models
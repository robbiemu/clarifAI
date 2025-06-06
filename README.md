# ClarifAI

AI-powered knowledge extraction and organization system for Obsidian vaults.

## Overview

ClarifAI is a monorepo containing multiple services that work together to process, analyze, and organize knowledge stored in Obsidian vaults. The system extracts claims, generates summaries, identifies concepts, and maintains a structured knowledge graph.

## Architecture

### Services

#### 🧠 clarifai-core
**Main processing engine** - Handles claim extraction, summarization, and concept linking.

- **Purpose**: Core AI processing pipeline
- **Responsibilities**: 
  - Extract claims from markdown documents
  - Generate summaries and concept definitions
  - Link claims to concepts using vector similarity
  - Manage the knowledge graph structure
- **Technologies**: Python, LLM integration, vector embeddings

#### 👁️ vault-watcher  
**File observer** - Monitors Obsidian vault for changes and triggers processing.

- **Purpose**: Real-time vault monitoring
- **Responsibilities**:
  - Watch for markdown file changes
  - Emit dirty block notifications
  - Coordinate with message broker for async processing
- **Technologies**: Python, file system monitoring, RabbitMQ

#### ⏰ scheduler
**Task scheduler** - Manages periodic jobs and background processing.

- **Purpose**: Automated job management
- **Responsibilities**:
  - Nightly concept hygiene and drift detection
  - Vault synchronization jobs
  - Batch reprocessing tasks
  - System maintenance operations
- **Technologies**: Python, job scheduling, cron-like functionality

#### 🖥️ clarifai-ui
**Gradio interface** - Web-based user interface for configuration and monitoring.

- **Purpose**: User interaction and system control
- **Responsibilities**:
  - Configuration panel for system settings
  - Processing status and monitoring
  - Manual job triggering
  - System diagnostics and reporting
- **Technologies**: Python, Gradio, web interface

### Shared Components

#### 📦 shared/
**Common utilities and data models** - Reusable components across all services.

- **Purpose**: Code reuse and consistency
- **Contains**:
  - Data models and schemas
  - Database connection utilities
  - Message queue interfaces
  - Common configuration handling
  - Utility functions and helpers

## Technology Stack

- **Language**: Python 3.11+
- **Package Management**: Poetry (workspace mode)
- **Code Quality**: Ruff, Black, MyPy, pre-commit
- **Testing**: pytest with coverage
- **Databases**: Neo4j (graph), PostgreSQL (vector store)
- **Message Broker**: RabbitMQ
- **Containerization**: Docker & Docker Compose

## Development Setup

### Prerequisites

- Python 3.11 or higher
- Poetry (latest version)
- Git

### Quick Start

1. **Clone the repository**:
   ```bash
   git clone https://github.com/robbiemu/clarifAI.git
   cd clarifAI
   ```

2. **Install dependencies**:
   ```bash
   poetry install
   ```

3. **Set up pre-commit hooks**:
   ```bash
   poetry run pre-commit install
   ```

4. **Run tests**:
   ```bash
   poetry run pytest
   ```

### Workspace Structure

```
clarifAI/
├── docs/                    # Documentation
├── services/                # Individual services
│   ├── clarifai-core/      # Main processing engine
│   ├── vault-watcher/      # File monitoring service
│   ├── scheduler/          # Task scheduling service
│   └── clarifai-ui/        # Gradio web interface
├── shared/                  # Shared utilities and models
├── tests/                   # Integration tests
├── pyproject.toml          # Root project configuration
├── .pre-commit-config.yaml # Code quality hooks
└── README.md               # This file
```

### Working with Services

Each service is a separate Python package that can be developed independently:

```bash
# Install all services in development mode
poetry install

# Run a specific service
cd services/clarifai-core
poetry run python -m clarifai_core

# Run tests for a specific service
cd services/vault-watcher  
poetry run pytest
```

### Code Quality

We use several tools to maintain code quality:

- **Ruff**: Fast Python linter and formatter
- **Black**: Code formatting
- **MyPy**: Static type checking
- **pre-commit**: Automated quality checks

Run quality checks manually:
```bash
poetry run ruff check .
poetry run black --check .
poetry run mypy .
```

## Deployment

The system is designed to run via Docker Compose for easy deployment:

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

See the [architecture documentation](docs/arch/architecture.md) for detailed deployment information.

## Contributing

1. Create a feature branch from `main`
2. Make your changes in the appropriate service directory
3. Ensure all tests pass and code quality checks succeed
4. Submit a pull request with a clear description

### Conventions

- Follow Python PEP 8 style guidelines
- Use type hints for all function signatures
- Write tests for new functionality
- Update documentation for user-facing changes
- Use conventional commit messages

## License

[License details to be added]

## Support

For questions and support, please refer to the project documentation in the `docs/` directory or open an issue on GitHub.
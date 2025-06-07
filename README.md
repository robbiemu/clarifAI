# ClarifAI

[![CI](https://github.com/robbiemu/clarifAI/workflows/CI/badge.svg)](https://github.com/robbiemu/clarifAI/actions/workflows/ci.yml)

ClarifAI is an AI-powered knowledge system designed to transform your scattered digital conversations (from chats, meeting transcripts, AI interactions, etc.) into a deeply interconnected and organized knowledge base directly within your Obsidian vault. It acts as an intelligent assistant that reads, understands, and links your conversational data, making it instantly accessible and actionable.

## Monorepo Structure

This repository is a monorepo containing the various services and shared libraries that constitute the ClarifAI system. This structure helps in managing dependencies and streamlining the development process across different components.

The main components are:

*   **`services/`**: Contains the individual microservices that make up ClarifAI's backend and UI.
    *   **`clarifai-core/`**: The main processing engine for ingestion, claim extraction, summarization, concept linking, and interaction with databases (vector store and knowledge graph).
    *   **`vault-watcher/`**: Monitors the Obsidian vault for Markdown file changes, emitting notifications to keep the system synchronized with the vault content.
    *   **`scheduler/`**: Runs periodic background jobs like concept hygiene, embedding refreshes, reprocessing dirty blocks, and vault-graph synchronization.
    *   **`clarifai-ui/`**: The user interface for ClarifAI, likely for importing data, managing configurations, and viewing system status/outputs.
*   **`shared/`**: Contains shared Python modules, data models, and utilities for use across different services.
*   **`docs/`**: Contains all project documentation, including technical overviews, architecture decision records, and product definitions.

## Technology Stack

*   **Language:** Python 3.11+
*   **Package Management:** uv
*   **Code Quality:** Ruff, MyPy (setup pending), pre-commit
*   **Testing:** pytest with coverage (setup pending)
*   **Databases:** Neo4j (graph), PostgreSQL (vector store)
*   **Message Broker:** RabbitMQ
*   **Containerization:** Docker & Docker Compose

## Development

### Getting Started

1. **Clone the repository:**
   ```bash
   git clone https://github.com/robbiemu/clarifAI.git
   cd clarifAI
   ```

2. **Set up the environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Install dependencies:**
   ```bash
   pip install -e ".[dev]"
   ```

4. **Run the stack:**
   ```bash
   docker compose up -d
   ```

### Continuous Integration

This project uses GitHub Actions for continuous integration. The CI pipeline automatically runs on every push and pull request to the `main` branch.

#### CI Pipeline Overview

The CI workflow includes:

1. **Code Quality Checks:**
   - **Ruff linting:** Ensures code follows style and quality standards
   - **Ruff formatting:** Validates code formatting consistency
   - **Black formatting:** Double-checks code formatting
   - **MyPy type checking:** Validates type annotations (currently permissive)
   - **Bandit security scanning:** Checks for common security issues

2. **Testing:**
   - **Unit tests:** Runs all test suites across services using pytest
   - **Coverage reporting:** Monitors test coverage for the codebase

3. **Docker Validation:**
   - **Individual service builds:** Validates each service's Dockerfile
   - **Docker Compose validation:** Ensures the full stack configuration is valid
   - **Multi-service build:** Tests building all services together

#### Running CI Checks Locally

You can run the same checks locally before submitting a pull request:

```bash
# Code quality checks
ruff check .
ruff format --check .
mypy .
bandit -r . -x tests/

# Run tests
python -m pytest

# Docker validation
docker compose config
docker compose build
```

#### Pre-commit Hooks

This project uses pre-commit hooks to ensure code quality. Install them with:

```bash
pre-commit install
```

The hooks will automatically run the same checks that are performed in CI.

## Documentation

Detailed project documentation, including architectural decisions, technical specifications, and sprint plans, can be found in the [`docs/`](./docs/) directory. The main entry point for documentation is [`docs/README.md`](./docs/README.md).

## License

This project is licensed under the GNU Lesser General Public License Version 3. See the [LICENSE](LICENSE) file for details.

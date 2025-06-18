# aclarai

[![CI](https://github.com/robbiemu/aclarai/workflows/CI/badge.svg)](https://github.com/robbiemu/aclarai/actions/workflows/ci.yml)

aclarai is an AI-powered knowledge system designed to transform your scattered digital conversations (from chats, meeting transcripts, AI interactions, etc.) into a deeply interconnected and organized knowledge base directly within your Obsidian vault. It acts as an intelligent assistant that reads, understands, and links your conversational data, making it instantly accessible and actionable.

**RECENT PROJECT RENAME** - When I started this project I named it clarifAI based on the name of a significant pattern I am making use of to select concepts: Microsoft's [claimify](https://arxiv.org/abs/2502.10855). However, [clarifai](https://www.clarifai.com) is its own AI-focused company with a trademark, as well as significant [open source contributions](https://github.com/clarifai). I'm not even 50% of my way through the MVP, not a single user has shown up to comment or contribute, so it is easy for me to rename the repo to something that will not be an issue. I am nearly certain that all necessary changes have been made. If you see that word anywhere in this repo please let me know.

## Monorepo Structure

This repository is a monorepo containing the various services and shared libraries that constitute the aclarai system. This structure helps in managing dependencies and streamlining the development process across different components.

The main components are:

*   **`services/`**: Contains the individual microservices that make up aclarai's backend and UI.
    *   **`aclarai-core/`**: The main processing engine for ingestion, claim extraction, summarization, concept linking, and interaction with databases (vector store and knowledge graph).
    *   **`vault-watcher/`**: Monitors the Obsidian vault for Markdown file changes, emitting notifications to keep the system synchronized with the vault content.
    *   **`scheduler/`**: Runs periodic background jobs like concept hygiene, embedding refreshes, reprocessing dirty blocks, and vault-graph synchronization.
    *   **`aclarai-ui/`**: The user interface for aclarai, likely for importing data, managing configurations, and viewing system status/outputs.
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
   git clone https://github.com/robbiemu/aclarai.git
   cd aclarai
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

The CI workflow includes four separate jobs for clear separation of concerns:

1. **Lint and Format:**
   - **Ruff linting:** Ensures code follows style and quality standards
   - **Ruff formatting:** Validates code formatting consistency
   - **MyPy type checking:** Validates type annotations (currently permissive)

2. **Security Scan:**
   - **Bandit security scanning:** Checks for common security vulnerabilities
   - **Configured to minimize false positives:** Uses `.bandit` config to skip assert usage in tests and intentional 0.0.0.0 bindings for containerized apps

3. **Testing:**
   - **Unit tests:** Runs all test suites across services using pytest
   - **Coverage reporting:** Monitors test coverage for the codebase

4. **Docker Validation:**
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

# Security scan
bandit -r . -c .bandit

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

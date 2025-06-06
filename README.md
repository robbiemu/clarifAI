# ClarifAI

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

## Documentation

Detailed project documentation, including architectural decisions, technical specifications, and sprint plans, can be found in the [`docs/`](./docs/) directory. The main entry point for documentation is [`docs/README.md`](./docs/README.md).

## License

This project is licensed under the GNU Lesser General Public License Version 3. See the [LICENSE](LICENSE) file for details.

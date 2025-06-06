# ClarifAI Core Service

Main processing engine for the ClarifAI knowledge extraction and organization system.

## Overview

The clarifai-core service is the heart of the ClarifAI system, responsible for:

- **Claim Extraction**: Analyzing markdown documents to extract meaningful claims and assertions
- **Summarization**: Generating concise summaries of document content 
- **Concept Linking**: Identifying and linking claims to relevant concepts using vector similarity
- **Knowledge Graph Management**: Maintaining the structured knowledge graph in Neo4j

## Architecture

### Components

- **Processing Pipeline**: Orchestrates the flow from document input to knowledge graph output
- **AI Integrations**: Interfaces with LLMs (OpenAI, Anthropic) for text processing
- **Vector Store**: Manages embeddings and similarity search using PostgreSQL with pgvector
- **Graph Database**: Stores and queries the knowledge graph using Neo4j
- **Message Handler**: Processes incoming messages from vault-watcher and scheduler

### Key Modules

```
clarifai_core/
├── __init__.py
├── main.py                 # Service entry point
├── pipeline/               # Processing pipeline
│   ├── __init__.py
│   ├── claim_extractor.py  # Extract claims from text
│   ├── summarizer.py       # Generate summaries
│   └── concept_linker.py   # Link claims to concepts
├── ai/                     # AI model integrations
│   ├── __init__.py
│   ├── llm_client.py       # LLM client wrapper
│   └── embeddings.py       # Embedding generation
├── storage/                # Database interfaces
│   ├── __init__.py
│   ├── graph_db.py         # Neo4j operations
│   └── vector_db.py        # PostgreSQL/pgvector operations
└── handlers/               # Message and event handlers
    ├── __init__.py
    └── message_handler.py   # RabbitMQ message processing
```

## Configuration

The service uses environment variables and configuration files for setup:

- `OPENAI_API_KEY`: OpenAI API credentials
- `ANTHROPIC_API_KEY`: Anthropic API credentials  
- `NEO4J_URI`: Neo4j database connection string
- `POSTGRES_URI`: PostgreSQL database connection string
- `RABBITMQ_HOST`: RabbitMQ broker hostname

## Dependencies

### Core Dependencies
- **LLM Clients**: openai, anthropic, langchain
- **Embeddings**: sentence-transformers
- **Databases**: neo4j, psycopg2-binary, pgvector
- **Data Models**: pydantic
- **Text Processing**: spacy, tiktoken

### Development Dependencies
- **Testing**: pytest, pytest-asyncio, pytest-mock
- **Shared Package**: clarifai-shared (local)

## Usage

### As a Service
```bash
cd services/clarifai-core
poetry install
poetry run python -m clarifai_core
```

### Development
```bash
# Run tests
poetry run pytest

# Type checking
poetry run mypy clarifai_core

# Linting
poetry run ruff check clarifai_core
```

## API Interface

The service exposes internal APIs for:
- Document processing requests
- Status and health checks
- Configuration updates
- Manual processing triggers

## Integration

Integrates with other ClarifAI services:
- **vault-watcher**: Receives file change notifications
- **scheduler**: Handles scheduled processing jobs
- **clarifai-ui**: Provides status and control interface
- **shared**: Uses common data models and utilities
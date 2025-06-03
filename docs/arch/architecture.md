# ClarifAI Deployment Architecture (Docker Compose Edition)

This document outlines a containerized architecture for **ClarifAI**, leveraging Docker Compose to manage heavy backend components such as Neo4j (graph DB), Postgres (vector DB), and scheduled automation jobs. This approach supports local and small-team deployments with strong isolation, observability, and development ergonomics.

---

## 🧱 Component Overview

| Service         | Purpose                                                                  |
| --------------- | ------------------------------------------------------------------------ |
| `vault-watcher` | Scans the Obsidian vault for Markdown changes, emits dirty block IDs     |
| `clarifai-core` | Main processing engine: claim extraction, summarization, concept linking |
| `postgres`      | Stores sentence/chunk embeddings via pgvector for vector search          |
| `neo4j`         | Holds the structured knowledge graph (claims, concepts, summaries, etc.) |
| `scheduler`     | Triggers nightly jobs (concept hygiene, vault sync, reprocessing)        |
| `reverse-proxy` | (Optional) For remote access, secure with HTTPS and auth                 |

---

## 🐳 Docker Compose Services

```yaml
# ClarifAI Docker Compose Stack
# no version: this is officially deprecated now

services:
  postgres:  # Vector DB backend for sentence embeddings and similarity checks
    image: ankane/pgvector
    restart: unless-stopped
    env_file:
      - .env
    environment:
      POSTGRES_DB: clarifai
    volumes:
      - pg_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    networks:
      - clarifai_net

  neo4j:  # Knowledge graph for claims, summaries, and concepts
    image: neo4j:5
    restart: unless-stopped
    env_file:
      - .env
    environment:
      NEO4J_AUTH: ${NEO4J_USER}/${NEO4J_PASSWORD}
    volumes:
      - neo4j_data:/data
    ports:
      - "7474:7474"
      - "7687:7687"
    networks:
      - clarifai_net

  rabbitmq: # Message broker for inter-service communication (e.g., vault-watcher -> clarifai-core)
    image: rabbitmq:3-management # Includes management UI on port 15672
    restart: unless-stopped
    environment:
      RABBITMQ_DEFAULT_USER: user # Replace with environment variables or Docker secrets
      RABBITMQ_DEFAULT_PASS: password # Replace with environment variables or Docker secrets
    ports:
      - "5672:5672" # Standard AMQP port
      - "15672:15672" # Management UI
    networks:
      - clarifai_net
    healthcheck: # Basic health check
      test: ["CMD", "rabbitmq-diagnostics", "ping"]
      interval: 30s
      timeout: 10s
      retries: 5

  clarifai-core:  # Main processing pipeline: claim extraction, summarization, linking
    build: ./clarifai-core
    depends_on:
      - postgres
      - neo4j
    volumes:
      - ../vault:/vault
    env_file:
      - .env
    networks:
      - clarifai_net
    environment:
      - VAULT_PATH=/vault
      - RABBITMQ_HOST=rabbitmq 

  vault-watcher:  # Watches vault for Markdown edits and emits dirty blocks
    build: ./vault-watcher
    depends_on:
      - clarifai-core
    volumes:
      - ../vault:/vault
    env_file:
      - .env
    networks:
      - clarifai_net
    environment:
      - VAULT_PATH=/vault
      - RABBITMQ_HOST=rabbitmq 

  scheduler:  # Runs periodic jobs: concept hygiene, vault sync, reprocessing
    build: ./scheduler
    depends_on:
      - clarifai-core
    volumes:
      - ../vault:/vault
    env_file:
      - .env
    networks:
      - clarifai_net
    environment:
      - VAULT_PATH=/vault

volumes:
  pg_data:
  neo4j_data:

networks:
  clarifai_net:
```

---

## ⏱️ Scheduled Jobs (via `scheduler`)

Nightly or periodic jobs are handled by a dedicated container that can:

* Refresh concept embeddings
* Detect and merge near-duplicate concepts
* Reprocess dirty Markdown blocks
* Reconcile Neo4j with file changes (vault-to-graph sync)

The scheduler uses `cron`, `celery beat`, or a lightweight alternative like [`watchfiles`](https://pypi.org/project/watchfiles/) + `APScheduler`.

---

## 🔄 Graph–Vault Synchronization

As described in \[on\_graph\_vault\_synchronization.md], the sync system must:

* Watch for changes in `.md` files
* Parse `clarifai:id` and `ver=` markers
* Update Neo4j nodes or queue jobs if blocks have changed
* Perform atomic writes (`.tmp` → `rename`) to ensure file safety

This sync logic is embedded within `vault-watcher` and executed by the nightly `scheduler`.

---

## 🧠 Concept Handling Strategy

Concept creation and drift merging (from \[on\_concepts.md]) runs in two modes:

* **During claim extraction batches:** extract surface candidates, check similarity (via HNSW), create or update `(:Concept)` nodes.
* **Nightly job:** refresh embeddings from Tier 3 files, detect/merge near-duplicates, handle file → graph hygiene.

---

## 📦 Build & Extend

* Each service has its own `Dockerfile`.
* Models (e.g. LLMs, embedders) can be configured via `.env` or mounted config files.
* Plugins for new file formats or additional graph analyses can mount as volumes or live in their own containers.

---

## 🔐 Security & Deployment Notes

* You can override any `.env` variable (e.g., database URLs) by setting it in your shell before running `docker compose`, or by mounting your own `.env` file.

* To use your own Neo4j or Postgres instance, set `GRAPH_DB_URL` and `VECTOR_DB_URL` in `.env`. When pointing to services outside Docker (e.g., on host), use `host.docker.internal` as the hostname inside containers.

* If your Neo4j or Postgres service is hosted remotely or outside this Compose stack, you may comment out or remove the corresponding service block in `docker-compose.yml` to avoid conflicts.

* Secrets (e.g. database passwords, auth tokens) should be stored in a `.env` file or managed with Docker secrets.

* The Docker Compose file now references these via `env_file` instead of hardcoded values.

* If deployed remotely, use a reverse proxy (e.g. Traefik or Caddy) to add HTTPS, rate limiting, and auth.

* Optional: expose a REST/gRPC API gateway for headless interaction.

---

## ✅ Summary

This Docker Compose setup cleanly separates ClarifAI’s data storage (Neo4j, Postgres), processing agents (claimify, summarizer, concept linker), and scheduling logic. It offers a reproducible local deployment and a strong base for small-team or remote usage.

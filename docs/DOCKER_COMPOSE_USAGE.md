# aclarai Docker Compose Stack

This guide provides instructions for running the aclarai Docker Compose stack locally.

## Overview

The Docker Compose stack includes the following services:

- **PostgreSQL with pgvector** (port 5432) - Vector database for sentence embeddings
- **Neo4j** (ports 7474, 7687) - Knowledge graph database for claims, concepts, and summaries
- **RabbitMQ** (ports 5672, 15672) - Message broker for inter-service communication
- **aclarai-core** - Main processing engine for claim extraction and concept linking
- **vault-watcher** - Monitors the vault directory for file changes
- **scheduler** - Runs periodic background jobs and maintenance tasks

## Prerequisites

- Docker (version 20.10 or later)
- Docker Compose (version 2.0 or later)
- At least 4GB of available RAM
- At least 2GB of available disk space

## Quick Start

1. **Clone the repository and navigate to the project root:**
   ```bash
   git clone <repository-url>
   cd aclarai
   ```

2. **Copy the environment file:**
   ```bash
   cp .env.example .env
   ```

3. **Install default configuration (optional):**
   ```bash
   cd services/aclarai-core
   python install/install_config.py
   cd ../..
   ```
   This creates `settings/aclarai.config.yaml` with default settings that you can customize.

4. **Edit configuration files (optional):**
   ```bash
   # Edit environment variables
   nano .env
   
   # Edit configuration settings
   nano settings/aclarai.config.yaml
   ```

5. **Start the entire stack:**
   ```bash
   docker compose up -d
   ```

6. **Check the status of all services:**
   ```bash
   docker compose ps
   ```

## Service-specific Commands

### Start only database services:
```bash
docker compose up postgres neo4j rabbitmq -d
```

### Start only application services:
```bash
docker compose up aclarai-core vault-watcher scheduler -d
```

### View logs for a specific service:
```bash
docker compose logs aclarai-core
docker compose logs vault-watcher
docker compose logs scheduler
```

### View logs for all services:
```bash
docker compose logs
```

### Stop all services:
```bash
docker compose down
```

### Stop and remove volumes (WARNING: This will delete all data):
```bash
docker compose down -v
```

## Service Access

### Neo4j
- **Browser interface:** http://localhost:7474
- **Bolt connection:** bolt://localhost:7687
- **Username:** neo4j
- **Password:** (configured in .env file)

### PostgreSQL
- **Host:** localhost
- **Port:** 5432
- **Database:** aclarai
- **Username:** aclarai
- **Password:** (configured in .env file)

### RabbitMQ
- **AMQP connection:** amqp://localhost:5672
- **Management interface:** http://localhost:15672
- **Username:** user
- **Password:** password

## Vault Directory

The `vault` directory in the project root is mounted to all services at `/vault`. This is where you should place your Markdown files for processing:

```bash
# Example: Add a markdown file to the vault
echo "# Sample Document" > vault/sample.md
echo "This is a test document for aclarai processing." >> vault/sample.md
```

The vault-watcher service will automatically detect changes to files in this directory.

## Configuration System

aclarai uses a three-tier configuration system:

### Initial Setup
On first startup, aclarai will automatically create `settings/aclarai.config.yaml` from the default template if it doesn't exist. You can also manually install it:

```bash
cd services/aclarai-core
python install/install_config.py
```

### Configuration Files
- **`settings/aclarai.config.yaml`** - Your customizable settings (created from template)
- **Default template** - Built-in defaults in the shared package (not user-visible)
- **`.env`** - Environment variables for database connections and secrets

### Restoring Defaults
If you need to reset your configuration:

```bash
# Delete user config (will be regenerated on next startup)
rm settings/aclarai.config.yaml

# Or force reinstall
cd services/aclarai-core
python install/install_config.py --force
```

## Environment Variables

Key environment variables that can be configured in `.env`:

```bash
# Database Configuration
POSTGRES_USER=aclarai
POSTGRES_PASSWORD=your_postgres_password
POSTGRES_DB=aclarai
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_neo4j_password

# Automation Configuration
AUTOMATION_PAUSE=false
CONCEPT_EMBEDDING_REFRESH_ENABLED=true
CONCEPT_EMBEDDING_REFRESH_CRON="0 3 * * *"

# Logging
LOG_LEVEL=INFO
```

## Health Checks

All custom services include health checks. You can verify service health with:

```bash
docker compose ps
```

Healthy services will show `(healthy)` in the status column.

## Troubleshooting

### Services won't start
1. Check if all required ports are available:
   ```bash
   netstat -tlnp | grep -E ':(5432|7474|7687|5672|15672)'
   ```

2. Check Docker resource limits (memory, disk space)

3. View service logs for error messages:
   ```bash
   docker compose logs <service-name>
   ```

### Permission issues with vault directory
```bash
# Fix permissions for the vault directory
sudo chown -R $USER:$USER vault/
chmod -R 755 vault/
```

### Database connection issues
1. Ensure services are fully started (may take 30-60 seconds)
2. Check if the services are healthy:
   ```bash
   docker compose ps
   ```
3. Test database connections manually

### Rebuilding services after code changes
```bash
# Rebuild and restart services
docker compose build
docker compose up -d
```

## Development

### Building individual services
```bash
docker compose build aclarai-core
docker compose build vault-watcher
docker compose build scheduler
```

### Viewing real-time logs
```bash
docker compose logs -f aclarai-core
```

### Running commands in containers
```bash
docker compose exec aclarai-core python -c "import aclarai_core; print('OK')"
```

## Data Persistence

The following data is persisted across container restarts:

- **PostgreSQL data:** Stored in the `pg_data` Docker volume
- **Neo4j data:** Stored in the `neo4j_data` Docker volume
- **Vault files:** Stored in the `./vault` directory on the host

## Security Notes

- The default configuration is for development only
- Change all default passwords in production
- Use Docker secrets or external secret management for production deployments
- Consider using a reverse proxy with SSL/TLS for remote access

## External Database Configuration

To use external PostgreSQL or Neo4j instances instead of the containerized versions:

1. Comment out the corresponding service in `docker-compose.yml`
2. Update the environment variables in `.env`:
   ```bash
   POSTGRES_HOST=your-external-postgres-host
   NEO4J_HOST=your-external-neo4j-host
   ```
3. For connections to databases running on the Docker host, use `host.docker.internal` as the hostname

## Support

For issues and questions:
1. Check the service logs first
2. Ensure all prerequisites are met
3. Review this documentation
4. Check the project's issue tracker
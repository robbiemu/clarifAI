# Environment Variable Configuration Guide

This document explains how ClarifAI services handle environment variable injection and external database connections.

## Overview

ClarifAI uses a shared configuration system that automatically loads environment variables from `.env` files and provides intelligent fallback handling for external database connections, particularly when using `host.docker.internal` for services running outside the Docker compose stack.

## Configuration System Features

### 1. Automatic .env File Loading

- Services automatically search for and load `.env` files using `python-dotenv`
- Search path: current directory → parent directories → until `.env` found
- Explicit file path can be specified: `load_config(env_file="/path/to/.env")`

### 2. External Database Fallback

When running inside Docker containers, the system automatically applies `host.docker.internal` fallback for external database connections:

- **Automatic detection**: Detects when running inside Docker (`.dockerenv` file or `DOCKER_CONTAINER=true`)
- **Smart fallback**: Applies `host.docker.internal` for external IPs and hostnames
- **Service preservation**: Keeps Docker service names unchanged (`postgres`, `neo4j`, etc.)

### 3. Environment Variable Validation

- Validates required variables at service startup
- Provides clear error messages for missing configuration
- Supports custom validation rules per service

### 4. Centralized Configuration

All services use the same configuration patterns through the `clarifai-shared` package:

```python
from clarifai_shared import load_config

# Load with validation (recommended for core services)
config = load_config(validate=True)

# Load without validation (for UI or optional services)
config = load_config(validate=False)
```

## Configuration Variables

### Required Variables

These variables must be set for services to start:

- `POSTGRES_PASSWORD` - PostgreSQL database password
- `NEO4J_PASSWORD` - Neo4j database password

### Database Configuration

#### PostgreSQL (Vector Store)
```bash
POSTGRES_HOST=postgres              # or external hostname/IP
POSTGRES_PORT=5432
POSTGRES_USER=clarifai
POSTGRES_PASSWORD=your_password_here
POSTGRES_DB=clarifai
```

#### Neo4j (Knowledge Graph)
```bash
NEO4J_HOST=neo4j                    # or external hostname/IP
NEO4J_BOLT_PORT=7687
NEO4J_HTTP_PORT=7474
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password_here
```

#### RabbitMQ (Message Broker)
```bash
RABBITMQ_HOST=rabbitmq              # or external hostname/IP
RABBITMQ_PORT=5672
RABBITMQ_USER=user
RABBITMQ_PASSWORD=password
```

### Service Configuration

```bash
VAULT_PATH=/vault                   # Path to vault directory
LOG_LEVEL=INFO                      # Logging level
DEBUG=false                         # Debug mode
```

### AI/ML Configuration

```bash
OPENAI_API_KEY=your_key_here        # For GPT models
ANTHROPIC_API_KEY=your_key_here     # For Claude models
CLAIMIFY_MODEL=gpt-4               # Primary model
FALLBACK_PLUGIN=ollama:gemma:2b     # Fallback model
```

## External Database Setup

### Using External PostgreSQL

1. Set external database variables in `.env`:
   ```bash
   POSTGRES_HOST=192.168.1.100        # Your PostgreSQL server IP
   POSTGRES_PORT=5432
   POSTGRES_USER=clarifai
   POSTGRES_PASSWORD=secure_password
   POSTGRES_DB=clarifai
   ```

2. Comment out or remove the `postgres` service from `docker-compose.yml`

3. When running in Docker, the system will automatically use `host.docker.internal`

### Using External Neo4j

1. Set external database variables in `.env`:
   ```bash
   NEO4J_HOST=192.168.1.101          # Your Neo4j server IP
   NEO4J_BOLT_PORT=7687
   NEO4J_HTTP_PORT=7474
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=secure_password
   ```

2. Comment out or remove the `neo4j` service from `docker-compose.yml`

3. When running in Docker, the system will automatically use `host.docker.internal`

### Manual host.docker.internal Configuration

You can explicitly set the hostname to use Docker's special hostname:

```bash
POSTGRES_HOST=host.docker.internal
NEO4J_HOST=host.docker.internal
```

## Database Connection URLs

The configuration system automatically generates proper connection URLs:

### PostgreSQL Connection URL
```python
config = load_config()
# Returns: postgresql://user:password@host:port/database
postgres_url = config.postgres.get_connection_url()
```

### Neo4j Bolt URL
```python
config = load_config()
# Returns: bolt://host:port
neo4j_url = config.neo4j.get_neo4j_bolt_url()
```

## Error Handling

### Missing Required Variables
```
ValueError: Missing required environment variables: POSTGRES_PASSWORD, NEO4J_PASSWORD. 
Please check your .env file or environment configuration.
```

### Configuration Validation
```python
# Check for missing variables before service startup
missing = config.validate_required_vars()
if missing:
    print(f"Missing variables: {missing}")
```

## Testing Configuration

### Test External Database Connection
```python
from clarifai_shared import load_config

config = load_config(validate=False)

print(f"PostgreSQL URL: {config.postgres.get_connection_url()}")
print(f"Neo4j Bolt URL: {config.neo4j.get_neo4j_bolt_url()}")
print(f"Running in Docker: {os.path.exists('/.dockerenv')}")
```

### Validate Configuration
```python
from clarifai_shared import load_config

try:
    config = load_config(validate=True)
    print("Configuration is valid!")
except ValueError as e:
    print(f"Configuration error: {e}")
```

## Best Practices

### Security
- Never commit `.env` files to version control
- Use strong passwords for database connections (use a password manager)
- Rotate API keys regularly
- Use Docker secrets in production deployments
- All test files use obviously fake credentials (e.g., `fake_test_password_123`)
- GitGuardian and similar security scanners should not flag placeholder values

#### Password Security Guidelines
```bash
# Generate secure passwords for production
openssl rand -base64 32  # For database passwords
openssl rand -base64 64  # For JWT secrets

# Example strong password patterns (for documentation only)
# PostgreSQL: Use password manager or generated string like "Kf8$mQ9#vL2@pR7"
# Neo4j: Use password manager or generated string like "Yx3&nB6!wM4$tZ9"
# RabbitMQ: Use password manager or generated string like "Cm7^hS2*qE8@rV5"
```

#### Testing Security
- Tests use clearly identifiable fake credentials
- Test passwords follow pattern: `fake_test_*_password_*`
- API keys in tests use format: `sk-fake_test_key_*` or `sk-ant-fake_test_key_*`
- All test credentials are obviously non-production values

### Development
- Copy `.env.example` to `.env` and customize
- Test external database connections before deployment
- Use `DEBUG=true` for detailed logging during development
- Validate configuration early in service startup

### Production
- Use external secret management systems
- Enable TLS/SSL for database connections
- Use reverse proxy with authentication
- Monitor configuration changes and access

## Troubleshooting

### Service Won't Start
1. Check for missing required environment variables
2. Verify database connectivity
3. Confirm `.env` file is in the correct location
4. Check Docker container vs host networking

### External Database Not Connecting
1. Verify `host.docker.internal` fallback is working
2. Check firewall rules on database server
3. Confirm database server allows external connections
4. Test connection from Docker container manually

### Environment Variables Not Loading
1. Confirm `.env` file exists and is readable
2. Check for syntax errors in `.env` file
3. Verify python-dotenv is installed
4. Ensure no conflicting environment variables

## Service-Specific Configuration

Each service can extend the base configuration with service-specific settings:

### ClarifAI UI Service
```python
from clarifai_ui.config import UIConfig

ui_config = UIConfig.from_env()
shared_config = ui_config.shared_config  # Access to database config
```

### Service Integration
```python
from clarifai_shared import load_config

def main():
    config = load_config(validate=True)
    
    # Use configuration
    postgres_conn = connect_postgres(config.postgres.get_connection_url())
    neo4j_driver = GraphDatabase.driver(config.neo4j.get_neo4j_bolt_url())
```
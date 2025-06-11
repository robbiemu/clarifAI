# Embedding Tests

This directory contains tests for the embedding module components.

## Integration Testing

Some tests in this directory support integration testing against real services using the `--integration` flag:

```bash
# Run with mocked dependencies (default)
pytest shared/tests/embedding/

# Run with real PostgreSQL service
pytest shared/tests/embedding/ --integration
```

### Integration Test Requirements

When running with `--integration` flag, the following services must be available:

- **PostgreSQL Database**
  - Host: localhost
  - Port: 5432
  - Database: test_db
  - Username: test_user
  - Password: test_pass
  - Must have pgvector extension installed

### Affected Test Files

- `test_storage.py` - Tests vector store operations
  - Without `--integration`: Uses mocked SQLAlchemy engine
  - With `--integration`: Connects to real PostgreSQL database with pgvector

- `test_embedding_init.py` - Tests embedding pipeline initialization
  - Without `--integration`: Uses mocked pipeline components
  - With `--integration`: Initializes real pipeline components

- `test_embedding_pipeline.py` - Tests embedding pipeline functionality
  - Without `--integration`: Uses mocked dependencies
  - With `--integration`: Uses real embedding and storage components

### CI/CD Behavior

The automated testing pipeline does NOT use the `--integration` flag, so it will run with mocked dependencies by default. Integration tests are intended for local development and manual verification against real services.
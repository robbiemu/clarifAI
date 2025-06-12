# Graph Tests

This directory contains tests for the graph module components.

## Integration Testing

Some tests in this directory support integration testing against real services using the `--integration` flag:

```bash
# Run with mocked dependencies (default)
pytest shared/tests/graph/

# Run with real Neo4j service
pytest shared/tests/graph/ --integration
```

### Integration Test Requirements

When running with `--integration` flag, the following services must be available:

- **Neo4j Database**
  - Host: localhost
  - Port: 7687
  - Username: neo4j
  - Password: test_pass

### Affected Test Files

- `test_neo4j_manager.py` - Tests Neo4j graph operations
  - Without `--integration`: Uses mocked Neo4j driver
  - With `--integration`: Connects to real Neo4j database

### CI/CD Behavior

The automated testing pipeline does NOT use the `--integration` flag, so it will run with mocked dependencies by default. Integration tests are intended for local development and manual verification against real services.
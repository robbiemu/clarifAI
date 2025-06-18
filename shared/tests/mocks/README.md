# Mock Services

This directory contains in-memory mock implementations of aclarai services for development and testing.

## Available Mock Services

### MockNeo4jGraphManager (`mock_neo4j_manager.py`)

In-memory replacement for Neo4j graph operations that stores nodes and relationships in Python dictionaries. Provides the same interface as the real Neo4jGraphManager for:

- Creating and updating concept nodes
- Managing relationships between concepts
- Running basic graph queries
- Node existence checking

### MockVectorStore (`mock_vector_store.py`)

In-memory replacement for vector similarity search that uses deterministic embeddings and cosine similarity. Supports:

- Adding concepts with embeddings
- Finding similar candidates using cosine similarity
- Configurable top-k search results
- Deterministic embedding generation for consistent testing

## Usage

### Basic Mock Services

Create empty mock services for custom testing scenarios:

```python
from tests.mocks import MockNeo4jGraphManager, MockVectorStore

# Create empty mock services
neo4j_manager = MockNeo4jGraphManager()
vector_store = MockVectorStore()

# Use with ClaimConceptLinker
from aclarai_shared.claim_concept_linking import ClaimConceptLinker

linker = ClaimConceptLinker(
    neo4j_manager=neo4j_manager,
    vector_store=vector_store,
)
```

### Pre-seeded Mock Services

For development and testing with realistic data, use the seeded services from `tests.utils.seed_mocks`:

```python
from tests.utils import get_seeded_mock_services

# Get mock services populated with golden test data
neo4j_manager, vector_store = get_seeded_mock_services()

# Contains 10 pre-defined concepts and 3 sample claims
# for consistent, repeatable testing
```

## Testing Benefits

- **Fast Development**: No database setup required for local development
- **Predictable Results**: Deterministic embeddings ensure consistent test outcomes
- **Test Isolation**: Each test gets fresh, independent mock instances
- **Production Compatibility**: Same interface as real services - just omit mock parameters for production

## Related Documentation

See `docs/guides/mock_services_guide.md` for comprehensive usage examples and development workflow guidance.
# Mock Services for Claim-Concept Linking Development

This document describes how to use the in-memory mock services provided for claim-concept linking development and testing.

## Overview

The mock services provide lightweight, in-memory implementations of the core aclarai services needed for claim-concept linking:

- **MockNeo4jGraphManager**: In-memory replacement for Neo4j graph operations
- **MockVectorStore**: In-memory replacement for vector similarity search
- **get_seeded_mock_services()**: Utility to get pre-populated mock services with golden test data

## Usage

### Basic Mock Services

You can create empty mock services for testing:

```python
from tests.mocks import MockNeo4jGraphManager, MockVectorStore

# Create empty mock services
neo4j_manager = MockNeo4jGraphManager()
vector_store = MockVectorStore()

# Use them with ClaimConceptLinker
from aclarai_shared.claim_concept_linking import ClaimConceptLinker

linker = ClaimConceptLinker(
    neo4j_manager=neo4j_manager,
    vector_store=vector_store,
)
```

### Seeded Mock Services

For development and testing with realistic data, use the seeded services:

```python
from tests.utils import get_seeded_mock_services

# Get mock services populated with golden test data
neo4j_manager, vector_store = get_seeded_mock_services()

# Use them with ClaimConceptLinker
linker = ClaimConceptLinker(
    neo4j_manager=neo4j_manager,
    vector_store=vector_store,
)

# The services now contain:
# - 10 concept candidates in the vector store
# - 10 concept nodes in Neo4j
# - 3 claim nodes in Neo4j
# - All with deterministic embeddings for consistent similarity search
```

### Golden Dataset

The seeded mock services include the following golden concepts:

- Machine Learning
- GPU Error
- CUDA Error
- Deep Learning
- Neural Networks
- Data Science
- Python Programming
- Database Optimization
- API Development
- Software Architecture

And sample claims:

- "The model failed to train due to GPU memory issues"
- "Deep learning requires large datasets for good performance"
- "CUDA 12.3 compatibility issues with the current driver"

## Development Workflow

1. **Local Development**: Use `get_seeded_mock_services()` to get a stable environment for developing claim-concept linking logic.

2. **Unit Testing**: Create fresh mock services for each test to ensure isolation.

3. **Integration Testing**: Use the seeded services to test the complete workflow with predictable data.

## Example: Finding Similar Concepts

```python
from tests.utils import get_seeded_mock_services

neo4j_manager, vector_store = get_seeded_mock_services()

# Find concepts similar to a query
results = vector_store.find_similar_candidates(
    "GPU memory error",
    top_k=3,
    similarity_threshold=0.5
)

# Results will include "GPU Error" and "CUDA Error" with high similarity
for doc, similarity in results:
    print(f"Concept: {doc['text']}, Similarity: {similarity:.3f}")
```

## Test Isolation

Mock services provide utilities for test isolation:

```python
def test_something():
    neo4j_manager, vector_store = get_seeded_mock_services()
    
    # ... test logic ...
    
    # Clear data for next test (if needed)
    neo4j_manager.clear_all_data()
    vector_store.clear_all_data()
```

## Mock Service Features

### MockNeo4jGraphManager

- **In-memory storage**: Claims, concepts, sentences stored in dictionaries
- **Query execution**: Basic Cypher query simulation
- **CRUD operations**: Create/read operations for all node types
- **Query history**: Track executed queries for debugging

### MockVectorStore

- **Deterministic embeddings**: Same text always produces same embedding
- **Cosine similarity**: Real similarity calculation for realistic results
- **Status tracking**: Update and filter candidates by status
- **Metadata support**: Full metadata storage and retrieval

## Production vs Development

- **Development/Testing**: Use mock services for fast, reliable, isolated development
- **Production**: Initialize `ClaimConceptLinker` without mock parameters to use real Neo4j and PostgreSQL services

```python
# Development
neo4j_manager, vector_store = get_seeded_mock_services()
linker = ClaimConceptLinker(neo4j_manager=neo4j_manager, vector_store=vector_store)

# Production
linker = ClaimConceptLinker()  # Uses real services with config
```
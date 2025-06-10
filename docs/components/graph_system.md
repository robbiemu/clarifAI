# Neo4j Graph System

The graph system provides functionality for creating and managing (:Claim) and (:Sentence) nodes in the ClarifAI Neo4j knowledge graph.

## Overview

The graph management module provides:

- **Data Models**: `Claim`, `Sentence`, `ClaimInput`, `SentenceInput` for structured node data
- **Neo4j Manager**: `Neo4jGraphManager` for database operations 
- **Schema Management**: Automatic constraint and index creation
- **Batch Operations**: Efficient batch creation using Cypher UNWIND
- **Relationship Management**: Automatic `ORIGINATES_FROM` relationships to Block nodes

## Architecture

This implementation follows the architectural guidelines from `docs/arch/idea-neo4J-ineteraction.md`, using **Neo4j Python Driver (Direct Cypher)** for:

- Precise control over node properties including nullable evaluation scores
- Batch operations with UNWIND for performance
- Complex property types and relationships
- Schema management with constraints and indexes

## Data Models

### ClaimInput

Input data for creating Claim nodes:

```python
from clarifai_shared.graph import ClaimInput

claim_input = ClaimInput(
    text="The Earth orbits the Sun",
    block_id="block_conversation_123_chunk_5",
    entailed_score=0.95,
    coverage_score=0.88,
    decontextualization_score=0.92
)
```

Properties:
- `text`: The claim text content
- `block_id`: ID of the originating Block node 
- `entailed_score`: Optional float (0.0-1.0) - NLI entailment score
- `coverage_score`: Optional float (0.0-1.0) - Information completeness score
- `decontextualization_score`: Optional float (0.0-1.0) - Context independence score
- `claim_id`: Optional string - Auto-generated if not provided

### SentenceInput

Input data for creating Sentence nodes:

```python
from clarifai_shared.graph import SentenceInput

sentence_input = SentenceInput(
    text="This statement is ambiguous and unclear",
    block_id="block_conversation_123_chunk_8", 
    ambiguous=True,
    verifiable=False
)
```

Properties:
- `text`: The sentence text content
- `block_id`: ID of the originating Block node
- `ambiguous`: Optional boolean - Whether the sentence is ambiguous
- `verifiable`: Optional boolean - Whether the sentence is verifiable
- `sentence_id`: Optional string - Auto-generated if not provided

## Basic Usage

### Setup

```python
from clarifai_shared.graph import Neo4jGraphManager, ClaimInput, SentenceInput
from clarifai_shared.config import load_config

# Load configuration
config = load_config()

# Create graph manager
with Neo4jGraphManager(config) as graph:
    # Setup schema (constraints and indexes)
    graph.setup_schema()
    
    # Now ready for operations...
```

### Creating Claims

```python
# Prepare claim inputs from Claimify pipeline output
claim_inputs = [
    ClaimInput(
        text="Python is a programming language",
        block_id="block_conv_001_chunk_3",
        entailed_score=0.98,
        coverage_score=0.95,
        decontextualization_score=0.87
    ),
    ClaimInput(
        text="Machine learning requires data",
        block_id="block_conv_001_chunk_7", 
        entailed_score=0.92,
        coverage_score=0.88,
        decontextualization_score=0.94
    )
]

# Create claims in batch
claims = graph.create_claims(claim_inputs)
print(f"Created {len(claims)} claims")
```

### Creating Sentences

```python
# Prepare sentence inputs for non-claim utterances
sentence_inputs = [
    SentenceInput(
        text="Hmm, that's interesting",
        block_id="block_conv_001_chunk_12",
        ambiguous=True,
        verifiable=False
    ),
    SentenceInput(
        text="What do you think about this?",
        block_id="block_conv_001_chunk_15",
        ambiguous=False,
        verifiable=False
    )
]

# Create sentences in batch
sentences = graph.create_sentences(sentence_inputs)
print(f"Created {len(sentences)} sentences")
```

### Retrieving Nodes

```python
# Get claim by ID
claim_data = graph.get_claim_by_id("claim_abc123")
if claim_data:
    print(f"Found claim: {claim_data['text']}")

# Get sentence by ID  
sentence_data = graph.get_sentence_by_id("sentence_xyz789")
if sentence_data:
    print(f"Found sentence: {sentence_data['text']}")

# Get node counts for monitoring
counts = graph.count_nodes()
print(f"Graph contains: {counts['claims']} claims, {counts['sentences']} sentences")
```

## Schema

### Node Properties

#### Claim Nodes
```cypher
(:Claim {
    id: String,                        // Unique identifier
    text: String,                      // Claim text content
    entailed_score: Float,             // 0.0-1.0 or null
    coverage_score: Float,             // 0.0-1.0 or null  
    decontextualization_score: Float,  // 0.0-1.0 or null
    version: Integer,                  // Version number (starts at 1)
    timestamp: DateTime                // Creation timestamp
})
```

#### Sentence Nodes
```cypher
(:Sentence {
    id: String,           // Unique identifier
    text: String,         // Sentence text content
    ambiguous: Boolean,   // Whether sentence is ambiguous (or null)
    verifiable: Boolean,  // Whether sentence is verifiable (or null)
    version: Integer,     // Version number (starts at 1)
    timestamp: DateTime   // Creation timestamp
})
```

### Relationships

Both Claims and Sentences have `ORIGINATES_FROM` relationships to their source Block nodes:

```cypher
(:Claim)-[:ORIGINATES_FROM]->(:Block)
(:Sentence)-[:ORIGINATES_FROM]->(:Block)
```

### Constraints and Indexes

The schema setup creates:

**Constraints:**
- `claim_id_unique`: Ensures Claim IDs are unique
- `sentence_id_unique`: Ensures Sentence IDs are unique

**Indexes:**
- `claim_text_index`: Index on Claim text for search performance
- `sentence_text_index`: Index on Sentence text for search performance  
- `claim_entailed_score_index`: Index on entailed_score for filtering
- `claim_coverage_score_index`: Index on coverage_score for filtering
- `claim_decontextualization_score_index`: Index on decontextualization_score for filtering

## Integration with Claimify Pipeline

This module is designed to integrate with the Claimify claim extraction pipeline:

1. **Claimify Output Processing**: Convert Claimify claim extraction results into `ClaimInput` objects
2. **Quality Score Handling**: Store evaluation scores (`entailed_score`, `coverage_score`, `decontextualization_score`) as nullable fields
3. **Fallback Sentence Creation**: Create `SentenceInput` objects for utterances that didn't produce high-quality claims
4. **Batch Processing**: Use batch operations for efficient database writes

## Error Handling

The module includes comprehensive error handling:

- **Connection Errors**: Proper handling of Neo4j connection failures
- **Authentication Errors**: Clear error messages for auth problems
- **Validation**: Input validation for required fields
- **Graceful Degradation**: Null score handling for failed evaluation agents

## Performance Considerations

- **Batch Operations**: All creation operations use Cypher UNWIND for efficient batch processing
- **Indexes**: Comprehensive indexing on frequently queried properties
- **Connection Management**: Context managers for proper resource cleanup
- **Transaction Safety**: All operations are transactional

## Configuration

Neo4j connection settings are managed through the ClarifAI configuration system:

```yaml
databases:
  neo4j:
    host: "neo4j"      # NEO4J_HOST environment variable
    port: 7687         # NEO4J_BOLT_PORT environment variable
    # NEO4J_USER and NEO4J_PASSWORD from environment
```

Environment variables:
- `NEO4J_HOST`: Neo4j server hostname
- `NEO4J_BOLT_PORT`: Neo4j bolt port (default: 7687)
- `NEO4J_USER`: Neo4j username
- `NEO4J_PASSWORD`: Neo4j password

## Implementation Details

The graph system is implemented in `shared/clarifai_shared/graph/`:

- `models.py`: Data models for Claims and Sentences
- `neo4j_manager.py`: Neo4j operations manager
- `__init__.py`: Module initialization and exports

For detailed usage examples, see the [Neo4j Graph Tutorial](../tutorials/neo4j_graph_tutorial.md).
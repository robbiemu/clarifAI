# Neo4j Graph Integration for ClarifAI

This directory contains the Neo4j graph management components that integrate with the Claimify pipeline to persist claims and sentences to the knowledge graph, as required for Sprint 3.

## 🏗️ Architecture

The integration follows the architecture defined in `docs/arch/idea-neo4J-ineteraction.md` and implements the requirements from Sprint 3 tasks:
- `sprint_3-Implement_core_ClaimifAI_pipeline.md`
- `sprint_3-Create_nodes_in_neo4j.md`

## 📂 Components

### Data Models (`data_models.py`)
- **`ClaimInput`**: Input data for creating (:Claim) nodes with quality scores
- **`SentenceInput`**: Input data for creating (:Sentence) nodes for failed claims
- **`BlockNodeInput`**: Input data for creating (:Block) nodes (Tier 1 sources)
- **`GraphNodeInput`**: Base class for all graph node inputs

### Graph Manager (`manager.py`)
- **`Neo4jGraphManager`**: Core Neo4j interaction using direct Cypher queries
- Provides batch operations for efficient node creation
- Handles schema application, constraints, and indexes
- Mock functionality for testing without Neo4j connection

### Integration (`../claimify/integration.py`)
- **`ClaimifyGraphIntegration`**: Connects Claimify pipeline to Neo4j
- Converts `ClaimifyResult` objects to graph input data
- Handles persistence of claims and sentences with proper relationships

## 🚀 Key Features

### Batch Operations
All node creation uses efficient `UNWIND` Cypher queries for batch processing:
- `create_claims_in_batch()`: Creates (:Claim) nodes with ORIGINATES_FROM relationships
- `create_sentences_in_batch()`: Creates (:Sentence) nodes with ORIGINATES_FROM relationships
- `create_blocks_in_batch()`: Creates (:Block) nodes for Tier 1 content

### Schema Management
- Automatic constraint creation for unique IDs
- Performance indexes on frequently queried properties
- Compatible with `docs/arch/graph_schema.cypher`

### Quality Score Integration
- Claims store evaluation scores (`entailed_score`, `coverage_score`, `decontextualization_score`)
- Scores initially `null`, populated by evaluation agents in Sprint 7
- Sentences track rejection reasons and quality flags

### Relationship Handling
- (:Claim)-[:ORIGINATES_FROM]->(:Block)
- (:Sentence)-[:ORIGINATES_FROM]->(:Block)
- Automatic (:Block) node creation when needed

## 🧪 Testing

Comprehensive test suite covers:
- **Data model conversion** (87 tests total)
- **Graph manager operations**
- **End-to-end integration workflows**
- **Error handling and edge cases**
- **Mock functionality for CI/CD**

Run tests with:
```bash
python -m unittest discover shared/tests/graph -v
python -m unittest discover shared/tests/claimify -v
```

## 🔧 Usage Example

```python
from clarifai_shared.claimify import (
    ClaimifyPipeline, 
    ClaimifyGraphIntegration,
    create_graph_manager_from_config
)

# Initialize components
config = load_config_from_yaml("settings/clarifai.config.yaml")
pipeline = ClaimifyPipeline()
graph_manager = create_graph_manager_from_config(config)
integration = ClaimifyGraphIntegration(graph_manager)

# Process sentences
results = pipeline.process_sentences(sentence_chunks)

# Persist to Neo4j
claims_created, sentences_created, errors = integration.persist_claimify_results(results)
```

See `complete_example.py` for a full workflow demonstration.

## 🗄️ Neo4j Schema

The implementation creates the following node types:

### (:Claim) Nodes
```cypher
(:Claim {
  id: "claim_12345678",
  text: "The system failed at startup",
  entailed_score: null,        // Set by evaluation agents
  coverage_score: null,
  decontextualization_score: null,
  verifiable: true,
  self_contained: true,
  context_complete: true,
  version: 1,
  timestamp: "2024-01-01T12:00:00"
})
```

### (:Sentence) Nodes
```cypher
(:Sentence {
  id: "sent_12345678", 
  text: "What should we do?",
  ambiguous: false,
  verifiable: false,
  failed_decomposition: false,
  rejection_reason: "Question format",
  version: 1,
  timestamp: "2024-01-01T12:00:00"
})
```

### (:Block) Nodes
```cypher
(:Block {
  id: "blk_001",
  text: "Original block content",
  content_hash: "abc123",
  source_file: "/vault/file.md",
  needs_reprocessing: false,
  version: 1,
  timestamp: "2024-01-01T12:00:00",
  last_synced: null
})
```

## 🔗 Integration Points

### Ready for Sprint 7 (Evaluation Agents)
- Claim nodes have placeholder scores ready for evaluation
- Structured output supports entailment, coverage, and decontextualization scoring

### Ready for Sprint 6 (Configuration Panel)
- Model injection architecture allows UI control of LLM selection
- Configuration structure matches `design_config_panel.md`

### Ready for Sprint 5 (Concept Linking)
- Claim nodes ready for SUPPORTS_CONCEPT, MENTIONS_CONCEPT relationships
- Consistent ID scheme for relationship creation

## 📋 Configuration

Configuration follows the structure in `settings/clarifai.config.yaml`:

```yaml
databases:
  neo4j:
    host: "neo4j"
    port: 7687
    # Credentials from environment variables:
    # NEO4J_USER, NEO4J_PASSWORD

model:
  claimify:
    default: "gpt-3.5-turbo"
    selection: null
    disambiguation: null
    decomposition: null

window:
  claimify:
    p: 3  # Previous sentences
    f: 1  # Following sentences

processing:
  claimify:
    max_retries: 3
    timeout_seconds: 30
    temperature: 0.1
```

## 🔒 Security & Resilience

- Connection credentials from environment variables only
- Graceful fallback to mock mode for testing
- Comprehensive error handling with retries
- Atomic operations using Neo4j transactions
- Structured logging following `docs/arch/idea-logging.md`

## 🚦 Status

✅ **Complete**: Sprint 3 core Claimify pipeline with Neo4j integration
- All 87 tests passing
- End-to-end workflow functional
- Schema and constraints applied
- Batch operations optimized
- Mock mode for CI/CD environments

🔄 **Ready for Integration**: 
- Sprint 7 evaluation agents (claim scoring)
- Sprint 6 configuration panel (model selection)
- Sprint 5 concept linking (relationship creation)
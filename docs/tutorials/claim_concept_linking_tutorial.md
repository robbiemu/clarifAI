# Claim-Concept Linking Tutorial

This tutorial walks you through using the claim-concept linking system to establish semantic relationships between claims and concepts using LLM-based classification.

## Prerequisites

Before starting, ensure you have:

1. **Neo4j database** - Either via Docker Compose or local installation with claim and concept data
2. **Environment configured** - `.env` file with database credentials and LLM API keys
3. **Dependencies installed** - Run `uv pip install -r shared/requirements.txt`

## Setting Up Your Environment

### Option 1: Using Docker Compose (Recommended)

The easiest way to get started is using the project's Docker Compose setup:

```bash
# Start the Neo4j service
docker-compose up neo4j -d

# The database will be automatically configured
```

### Option 2: Manual Setup

If you're using mock services for development/testing:

```python
from tests.utils import get_seeded_mock_services
from aclarai_shared.claim_concept_linking import ClaimConceptLinker

# Get pre-populated mock services
neo4j_manager, vector_store = get_seeded_mock_services()
```

### Environment Configuration

Create a `.env` file in the project root:

```bash
# Neo4j configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_secure_password

# LLM API configuration
OPENAI_API_KEY=your_openai_api_key
```

## Basic Usage

### Step 1: Initialize the Linker

```python
from aclarai_shared.claim_concept_linking import ClaimConceptLinker

# Using default configuration (production)
linker = ClaimConceptLinker()

# Or with mock services (development/testing)
from tests.utils import get_seeded_mock_services
neo4j_manager, vector_store = get_seeded_mock_services()

linker = ClaimConceptLinker(
    neo4j_manager=neo4j_manager,
    vector_store=vector_store,
)
```

### Step 2: Link Claims to Concepts

```python
# Process up to 100 claims with configurable thresholds
results = linker.link_claims_to_concepts(
    max_claims=100,
    similarity_threshold=0.7,    # Minimum concept similarity
    strength_threshold=0.5,      # Minimum relationship strength
)

print(f"Processed {results['claims_processed']} claims")
print(f"Created {results['relationships_created']} relationships")
print(f"Updated {results['markdown_files_updated']} Tier 2 files")
```

### Step 3: Review Results

The system creates three types of relationships:
- `SUPPORTS_CONCEPT`: The claim directly supports or affirms the concept
- `MENTIONS_CONCEPT`: The claim is related to the concept but neutral
- `CONTRADICTS_CONCEPT`: The claim contradicts the concept

## Advanced Usage

### Custom Configuration

```python
from aclarai_shared.config import load_config

# Load custom configuration
config = load_config()

# Initialize with custom settings
linker = ClaimConceptLinker(config=config)
```

### Working with Specific Claims

```python
# Get unlinked claims
unlinked_claims = linker.neo4j_manager.get_unlinked_claims(limit=10)

for claim in unlinked_claims:
    print(f"Claim: {claim['text'][:100]}...")
    
    # Find candidate concepts for this claim
    candidates = linker.find_candidate_concepts(
        claim_text=claim['text'],
        top_k=5
    )
    
    for candidate in candidates:
        print(f"  - {candidate.name} (similarity: {candidate.similarity:.3f})")
```

### Error Handling

The system handles various error scenarios gracefully:

```python
try:
    results = linker.link_claims_to_concepts()
except Exception as e:
    print(f"Linking failed: {e}")
    # System continues processing other claims
```

## Understanding the Results

### Relationship Metadata

Each created relationship includes:
- **Strength**: LLM-assessed confidence (0.0-1.0)
- **Entailed Score**: Copied from source claim (may be null)
- **Coverage Score**: Copied from source claim (may be null)

### File Updates

The system automatically updates Tier 2 Markdown files by:
- Adding `[[concept]]` wikilinks where relationships are created
- Preserving `aclarai:id` anchors
- Incrementing version numbers (`ver=N`)

## Monitoring and Debugging

### Logging

The system provides structured logging with context:

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Run linking with detailed output
results = linker.link_claims_to_concepts()
```

### Performance Metrics

Monitor the results dictionary for insights:

```python
results = linker.link_claims_to_concepts()

# Check processing efficiency
print(f"Relationship rate: {results['relationships_created'] / results['claims_processed']:.2f}")

# Monitor error rates
if 'errors' in results:
    print(f"Error rate: {len(results['errors']) / results['claims_processed']:.2f}")
```

## Next Steps

1. **Integration**: Deploy to aclarai-core service for automated processing
2. **Monitoring**: Set up alerts for relationship creation rates
3. **Quality**: Review created relationships and adjust thresholds as needed

For more details on the architecture and implementation, see the [claim-concept linking component documentation](../components/claim_concept_linking.md).
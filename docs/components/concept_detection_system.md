# HNSW-based Concept Detection System

This document describes the HNSW-based concept detection system implemented for aclarai, which uses hnswlib for fast similarity search and concept deduplication.

## Overview

The concept detection system analyzes noun phrase candidates extracted from Claims and Summary nodes to determine whether they should be:
- **Merged** with existing similar concepts (similarity ≥ 0.9)
- **Promoted** to new canonical concepts (no sufficient similarity found)

## Architecture

### Components

1. **ConceptDetector** (`shared/aclarai_shared/concept_detection/detector.py`)
   - Core component using hnswlib for similarity search
   - Builds and manages HNSW index from concept candidates
   - Provides similarity-based decision logic

2. **ConceptProcessor** (`services/aclarai-core/aclarai_core/concept_processor.py`)
   - Integration component for aclarai-core pipeline
   - Orchestrates noun phrase extraction, storage, and concept detection
   - Handles batch processing and status updates

3. **Data Models** (`shared/aclarai_shared/concept_detection/models.py`)
   - `ConceptAction`: Enum for merge/promote actions
   - `SimilarityMatch`: Represents similarity matches between candidates
   - `ConceptDetectionResult`: Results for individual candidates
   - `ConceptDetectionBatch`: Results for batch processing

### Integration Points

The concept detection system integrates with:
- **Noun Phrase Extraction**: Uses extracted candidates as input
- **Concept Candidates Store**: Stores and retrieves candidates with embeddings
- **DirtyBlockConsumer**: Processes concepts during block synchronization
- **Configuration System**: Uses configurable similarity thresholds

## Configuration

### Similarity Thresholds

Configured in `shared/aclarai_shared/config.py`:

```python
@dataclass
class ConceptsConfig:
    similarity_threshold: float = 0.9  # Threshold for merge decisions
    
@dataclass  
class ThresholdConfig:
    concept_merge: float = 0.90  # Alternative threshold setting
```

### HNSW Parameters

The HNSW index uses these parameters for optimal performance:

```python
# Index creation parameters
M=16                    # Number of connections per node
ef_construction=200     # Size of candidate set during construction
ef_search=50           # Search parameter for queries
space='cosine'         # Distance metric for embeddings
```

## Usage

### Basic Concept Detection

```python
from aclarai_shared.concept_detection import ConceptDetector
from aclarai_shared.noun_phrase_extraction.models import NounPhraseCandidate

# Initialize detector
detector = ConceptDetector()

# Build index from existing candidates
detector.build_index_from_candidates()

# Detect action for a candidate
candidate = NounPhraseCandidate(
    text="machine learning",
    normalized_text="machine learning", 
    source_node_id="claim_123",
    source_node_type="claim",
    aclarai_id="blk_456",
    embedding=[0.1] * 384
)

result = detector.detect_concept_action(candidate)
print(f"Action: {result.action.value}")  # "merged" or "promoted"
print(f"Confidence: {result.confidence}")
print(f"Reason: {result.reason}")
```

### Batch Processing

```python
# Process multiple candidates
candidates = [candidate1, candidate2, candidate3]
batch_result = detector.process_candidates_batch(candidates)

print(f"Merged: {batch_result.merged_count}")
print(f"Promoted: {batch_result.promoted_count}")
print(f"Processing time: {batch_result.processing_time}s")
```

### Integration with aclarai-core

```python
from aclarai_core.concept_processor import ConceptProcessor

# Initialize processor
processor = ConceptProcessor()

# Process a block for concepts
block = {
    "aclarai_id": "blk_123",
    "semantic_text": "Machine learning algorithms are used in AI applications.",
    "content_hash": "abc123",
    "version": 1
}

result = processor.process_block_for_concepts(block, "claim")
print(f"Candidates extracted: {result['candidates_extracted']}")
print(f"Actions: {result['concept_actions']}")
```

## Decision Logic

### Merge Decision

A candidate is marked for **merge** when:
1. Similar candidates exist in the index
2. Best similarity score ≥ similarity_threshold (default 0.9)
3. Matched candidate has sufficient confidence

### Promote Decision  

A candidate is marked for **promotion** when:
1. No similar candidates found, OR
2. Best similarity score < similarity_threshold
3. Candidate represents a genuinely new concept

### Similarity Calculation

The system uses cosine similarity between embeddings:
- Distance calculation: `distance = 1 - cosine_similarity`
- Similarity score: `similarity = 1 - distance`
- Uses hnswlib's optimized cosine distance implementation

## Performance Considerations

### Index Size

- **Initial size**: Configurable (default 10,000 elements)
- **Dynamic growth**: Automatically sized based on candidate count
- **Memory usage**: ~4KB per 384-dimensional embedding

### Search Performance

- **Query time**: O(log n) approximate nearest neighbor search
- **Batch processing**: Optimized for processing multiple candidates
- **Index rebuild**: Required when adding many new candidates

### Monitoring

Key metrics to monitor:
- Index size (`detector.id_to_metadata`)
- Processing time per batch
- Merge rate vs promotion rate
- Memory usage of HNSW index

## Error Handling

The system implements robust error handling:

1. **Index failures**: Graceful degradation to LlamaIndex fallback
2. **Embedding issues**: Skip candidates without embeddings
3. **Similarity errors**: Default to promotion on errors
4. **Batch processing**: Individual failures don't stop batch

## Testing

### Unit Tests

- **ConceptDetector**: 13 tests covering all core functionality
- **Models**: 7 tests for data structures
- **ConceptProcessor**: 9 tests for integration logic



### Running Tests

```bash
# Run concept detection tests
uv run pytest shared/tests/concept_detection/ -v

# Run integration tests  
uv run pytest services/aclarai-core/tests/test_concept_processor.py -v
```



## Dependencies

- **hnswlib**: Fast approximate nearest neighbor search
- **numpy**: Array operations for embeddings  
- **aclarai_shared**: Configuration and data models
- **LlamaIndex**: Fallback vector operations

## References

- [HNSW Algorithm Paper](https://arxiv.org/abs/1603.09320)
- [hnswlib Library](https://github.com/nmslib/hnswlib)
- [Concept Architecture](docs/arch/on-concepts.md)
# ClarifAI Embedding System Documentation

This document provides comprehensive documentation for the ClarifAI embedding system, which implements utterance chunk embedding and vector storage following the Sprint 2 requirements.

## Overview

The embedding system processes Tier 1 Markdown content by:

1. **Chunking** utterance blocks using LlamaIndex SentenceSplitter with semantic coherence rules
2. **Embedding** chunks using configurable HuggingFace models
3. **Storing** vectors in PostgreSQL with pgvector extension and proper metadata
4. **Querying** stored embeddings for similarity search

## Architecture

The system follows the ClarifAI architecture principles:

- **Configuration-driven**: All parameters configurable via `clarifai.config.yaml`
- **LlamaIndex-first**: Uses LlamaIndex abstractions for consistency
- **Reusable**: Placed in shared library for cross-service usage
- **Resilient**: Graceful error handling and fallbacks
- **Logged**: Structured logging with service context

## Components

### 1. UtteranceChunker

Segments Tier 1 Markdown blocks into coherent chunks following `docs/arch/on-sentence_splitting.md`.

**Key Features:**
- LlamaIndex SentenceSplitter as base layer
- Post-processing rules for semantic coherence
- Configurable chunk size and overlap
- Preserves all content (no discards)

**Configuration:**
```yaml
embedding:
  chunking:
    chunk_size: 300          # Maximum tokens per chunk
    chunk_overlap: 30        # Overlap between chunks
    keep_separator: true     # Keep sentence separators
    merge_colon_endings: true    # Merge "text:" + continuation
    merge_short_prefixes: true   # Merge fragments < min_chunk_tokens
    min_chunk_tokens: 5         # Minimum tokens per chunk
```

### 2. EmbeddingGenerator

Generates embeddings using configurable HuggingFace models with batch processing.

**Key Features:**
- Configurable embedding models
- Automatic device detection (CPU/GPU/MPS)
- Batch processing for efficiency
- Embedding validation

**Configuration:**
```yaml
embedding:
  models:
    default: "sentence-transformers/all-MiniLM-L6-v2"
    # Alternative models:
    # large: "sentence-transformers/all-mpnet-base-v2"
    # multilingual: "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
  
  device: "auto"    # "auto", "cpu", "cuda", "mps"
  batch_size: 32    # Chunks to embed at once
```

### 3. ClarifAIVectorStore

PostgreSQL vector storage using LlamaIndex PGVectorStore with metadata handling.

**Key Features:**
- LlamaIndex PGVectorStore integration
- Automatic table and index creation
- Metadata preservation (clarifai:id, chunk_index, original text)
- Efficient similarity queries with IVFFlat indexing
- Batch operations

**Configuration:**
```yaml
embedding:
  pgvector:
    collection_name: "utterances"
    embed_dim: 384            # Dimension for all-MiniLM-L6-v2
    index_type: "ivfflat"
    index_lists: 100          # Number of lists for IVFFlat index
```

### 4. EmbeddingPipeline

Orchestrates the complete embedding workflow with error handling and metrics.

**Key Features:**
- End-to-end processing pipeline
- Comprehensive error handling
- Processing metrics and validation
- Single block and batch processing
- Similarity search interface

## Usage Examples

### Basic Usage

```python
from clarifai_shared.embedding import EmbeddingPipeline

# Initialize pipeline (loads config automatically)
pipeline = EmbeddingPipeline()

# Process Tier 1 Markdown content
tier1_content = """
<!-- clarifai:title=Example Conversation -->
<!-- clarifai:created_at=2024-01-01T10:00:00Z -->

Alice: This is an example utterance for testing.
<!-- clarifai:id=blk_abc123 ver=1 -->
^blk_abc123

Bob: And this is another utterance in the conversation.
<!-- clarifai:id=blk_def456 ver=1 -->
^blk_def456
"""

# Process through the pipeline
result = pipeline.process_tier1_content(tier1_content)

if result.success:
    print(f"Successfully processed {result.stored_chunks} chunks")
else:
    print(f"Processing failed: {result.errors}")
```

### Single Block Processing

```python
# Process a single utterance block
result = pipeline.process_single_block(
    text="This is a single utterance to embed.",
    clarifai_block_id="blk_single123",
    replace_existing=True
)

print(f"Processed {result.total_chunks} chunks")
```

### Similarity Search

```python
# Search for similar chunks
results = pipeline.search_similar_chunks(
    query_text="example utterance",
    top_k=5,
    similarity_threshold=0.8
)

for result in results:
    print(f"Block: {result['clarifai_block_id']}, "
          f"Score: {result['similarity_score']:.3f}")
```

### Pipeline Status

```python
# Check pipeline component health
status = pipeline.get_pipeline_status()
print(f"Overall status: {status['overall_status']}")

for component, info in status['components'].items():
    print(f"{component}: {info['status']}")
```

### Individual Components

```python
from clarifai_shared.embedding import UtteranceChunker, EmbeddingGenerator, ClarifAIVectorStore

# Use components individually
chunker = UtteranceChunker()
chunks = chunker.chunk_utterance_block("Text to chunk", "blk_test")

generator = EmbeddingGenerator()
embedded_chunks = generator.embed_chunks(chunks)

vector_store = ClarifAIVectorStore()
metrics = vector_store.store_embeddings(embedded_chunks)
```

## Configuration Reference

### Complete Configuration Example

```yaml
# clarifai.config.yaml
embedding:
  # Model configuration
  models:
    default: "sentence-transformers/all-MiniLM-L6-v2"
  
  # Processing settings
  device: "auto"
  batch_size: 32
  
  # PGVector settings
  pgvector:
    collection_name: "utterances"
    embed_dim: 384
    index_type: "ivfflat"
    index_lists: 100
  
  # Chunking configuration
  chunking:
    chunk_size: 300
    chunk_overlap: 30
    keep_separator: true
    merge_colon_endings: true
    merge_short_prefixes: true
    min_chunk_tokens: 5

# Database configuration
databases:
  postgres:
    host: "postgres"
    port: 5432
    database: "clarifai"
    # User and password from environment:
    # POSTGRES_USER, POSTGRES_PASSWORD
```

### Environment Variables

Required environment variables:

```bash
# Database credentials
POSTGRES_USER=clarifai
POSTGRES_PASSWORD=your_password

# Optional overrides
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=clarifai

# OpenAI API key (if using OpenAI models)
OPENAI_API_KEY=your_openai_key
```

## Metadata Schema

Each embedded chunk stores the following metadata:

```python
{
    "clarifai_block_id": "blk_abc123",      # Parent Tier 1 block ID
    "chunk_index": 0,                       # Ordinal within block
    "original_text": "Full original text", # Complete source text
    "model_name": "sentence-transformers/all-MiniLM-L6-v2",
    "embedding_dim": 384
}
```

## Error Handling

The system implements comprehensive error handling:

- **Graceful Fallbacks**: Component failures don't crash the pipeline
- **Detailed Logging**: Structured logs with service context
- **Retry Logic**: Automatic retries for transient failures
- **Validation**: Embedding quality checks and dimension validation
- **Metrics**: Processing statistics and error counts

## Performance Considerations

### Batch Processing

The system uses batch processing for efficiency:

```yaml
embedding:
  batch_size: 32  # Adjust based on available memory
```

### Device Selection

Automatic device detection optimizes performance:

```yaml
embedding:
  device: "auto"  # Automatically selects best available device
  # Options: "cpu", "cuda", "mps", "auto"
```

### Index Optimization

PGVector index settings for query performance:

```yaml
embedding:
  pgvector:
    index_type: "ivfflat"
    index_lists: 100  # Adjust based on data size
```

## Testing

The system includes comprehensive tests:

```bash
# Run embedding tests
python -m pytest shared/tests/embedding/ -v

# Run configuration tests  
python -m pytest shared/tests/test_config_yaml.py -v

# Run all shared library tests
python -m pytest shared/tests/ -v
```

## Integration

### With Vault Synchronization

The embedding system integrates with ClarifAI's vault synchronization:

```python
# In vault sync job
pipeline = EmbeddingPipeline()

for tier1_file in changed_tier1_files:
    content = read_file(tier1_file)
    result = pipeline.process_tier1_content(content)
    
    if not result.success:
        logger.error(f"Failed to embed {tier1_file}: {result.errors}")
```

### With Other Services

Services can use the embedding system for various tasks:

```python
# In clarifai-core service
from clarifai_shared.embedding import EmbeddingPipeline

pipeline = EmbeddingPipeline()

# Search for related chunks during claim extraction
related_chunks = pipeline.search_similar_chunks(
    query_text=claim_text,
    top_k=5,
    similarity_threshold=0.85
)
```

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Verify PostgreSQL is running and accessible
   - Check environment variables
   - Ensure pgvector extension is installed

2. **Model Loading Errors**
   - Check internet connectivity for model downloads
   - Verify model name in configuration
   - Check available disk space

3. **Memory Issues**
   - Reduce batch_size in configuration
   - Use smaller embedding models
   - Check available RAM

4. **Performance Issues**
   - Enable GPU acceleration if available
   - Adjust index_lists for larger datasets
   - Monitor database performance

### Debugging

Enable debug logging for detailed information:

```yaml
logging:
  level: "DEBUG"
```

Check pipeline status for component health:

```python
status = pipeline.get_pipeline_status()
print(status)
```

## Future Enhancements

The embedding system is designed for future extensions:

- **Multiple Model Support**: Support for different models per content type
- **Advanced Chunking**: More sophisticated chunking strategies
- **Distributed Processing**: Support for distributed embedding generation
- **Incremental Updates**: Efficient updates for changed content
- **Custom Embeddings**: Support for domain-specific embedding models
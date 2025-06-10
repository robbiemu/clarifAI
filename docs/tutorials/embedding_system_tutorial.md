# Embedding System Tutorial

This tutorial walks you through using the ClarifAI embedding system to process utterance chunks and store them as semantic vectors in PostgreSQL.

## Prerequisites

Before starting, ensure you have:

1. **PostgreSQL with pgvector extension** - Either via Docker Compose or local installation
2. **Environment configured** - `.env` file with database credentials
3. **Dependencies installed** - Run `pip install -r shared/requirements.txt`

## Setting Up Your Environment

### Option 1: Using Docker Compose (Recommended)

The easiest way to get started is using the project's Docker Compose setup:

```bash
# Start the PostgreSQL service with pgvector
docker-compose up postgres -d

# The database will be automatically configured with the vector extension
```

### Option 2: Manual PostgreSQL Setup

If you're using a local PostgreSQL installation:

```sql
-- Connect to your PostgreSQL instance
CREATE EXTENSION IF NOT EXISTS vector;
CREATE DATABASE clarifai;
```

**Note**: This manual setup is primarily for developers who want to configure their environment outside of the project's Docker infrastructure.

### Environment Configuration

Create a `.env` file in the project root:

```bash
# Database configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=clarifai
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password

# Optional: AI model API keys
OPENAI_API_KEY=your_openai_key_here
```

## Basic Usage

### 1. Initialize the Embedding Pipeline

```python
from clarifai_shared.embedding import EmbeddingPipeline
from clarifai_shared.config import load_config

# Load configuration
config = load_config()

# Initialize the pipeline
pipeline = EmbeddingPipeline(config)
```

### 2. Process Tier 1 Content

The embedding system is designed to work with Tier 1 Markdown utterance blocks:

```python
# Sample Tier 1 content with clarifai metadata
tier1_content = """
<!-- clarifai:title=Demo Conversation -->
<!-- clarifai:created_at=2024-01-15T10:00:00Z -->
<!-- clarifai:id=conv_001 -->

# Conversation Analysis

## User Intent Recognition

The user expressed interest in learning about machine learning fundamentals. 
They specifically mentioned wanting to understand neural networks and their applications.

## Key Topics Discussed

- Introduction to supervised learning
- Neural network architectures
- Training methodologies
- Practical applications in NLP

## Follow-up Actions

Schedule a deeper dive session on convolutional neural networks and their use in computer vision applications.
"""

# Process the content
try:
    results = pipeline.process_utterance(
        content=tier1_content,
        clarifai_id="conv_001",
        metadata={"source": "demo", "type": "conversation"}
    )
    
    print(f"Successfully processed {len(results)} chunks")
    for i, result in enumerate(results):
        print(f"Chunk {i+1}: {result['chunk_text'][:100]}...")
        
except Exception as e:
    print(f"Error processing content: {e}")
```

### 3. Perform Similarity Search

Once you have vectors stored, you can search for similar content:

```python
# Search for similar content
query = "machine learning neural networks"

try:
    similar_chunks = pipeline.similarity_search(
        query=query,
        limit=5,
        similarity_threshold=0.7
    )
    
    print(f"Found {len(similar_chunks)} similar chunks:")
    for chunk in similar_chunks:
        print(f"Score: {chunk.score:.3f}")
        print(f"Text: {chunk.text[:150]}...")
        print(f"Metadata: {chunk.metadata}")
        print("---")
        
except Exception as e:
    print(f"Error performing search: {e}")
```

## Advanced Configuration

### Customizing Chunk Settings

You can adjust chunking behavior through the configuration:

```yaml
# In settings/clarifai.config.yaml
embedding:
  chunking:
    chunk_size: 512        # Tokens per chunk
    chunk_overlap: 50      # Overlap between chunks
    min_chunk_size: 100    # Minimum chunk size
    paragraph_separator: "\n\n"
```

### Using Different Embedding Models

The system supports multiple embedding providers:

```yaml
embedding:
  model:
    provider: "huggingface"                    # or "openai", "sentence_transformers"
    model_name: "sentence-transformers/all-MiniLM-L6-v2"
    max_length: 512
    normalize_embeddings: true
```

### Configuring Vector Storage

PostgreSQL vector storage can be tuned for performance:

```yaml
embedding:
  storage:
    table_name: "clarifai_embeddings"
    vector_dimension: 384     # Must match model output
    distance_metric: "cosine" # or "l2", "inner_product"
    index_type: "ivfflat"     # Vector index for performance
```

## Working with Real Data

### Processing Multiple Utterances

For batch processing of multiple Tier 1 files:

```python
from pathlib import Path

def process_vault_directory(vault_path: str):
    """Process all Tier 1 files in a vault directory."""
    vault = Path(vault_path)
    
    for tier1_file in vault.glob("**/*_tier1.md"):
        try:
            # Read the file content
            content = tier1_file.read_text()
            
            # Extract clarifai:id from metadata
            clarifai_id = extract_clarifai_id(content)
            
            # Process with the pipeline
            results = pipeline.process_utterance(
                content=content,
                clarifai_id=clarifai_id,
                metadata={"source_file": str(tier1_file)}
            )
            
            print(f"Processed {tier1_file.name}: {len(results)} chunks")
            
        except Exception as e:
            print(f"Error processing {tier1_file.name}: {e}")

def extract_clarifai_id(content: str) -> str:
    """Extract clarifai:id from markdown metadata."""
    import re
    match = re.search(r'<!-- clarifai:id=([^-]+) -->', content)
    return match.group(1) if match else "unknown"
```

### Metadata Handling

The system automatically preserves important metadata:

```python
# Metadata is automatically included for each chunk
metadata_example = {
    "clarifai_id": "conv_001",           # Original utterance ID
    "chunk_index": 0,                    # Position in original content
    "original_length": 1250,             # Length of source content
    "chunk_tokens": 128,                 # Estimated tokens in chunk
    "processing_timestamp": "2024-01-15T10:30:00Z",
    "model_name": "all-MiniLM-L6-v2",   # Embedding model used
    # Plus any custom metadata you provide
}
```

## Troubleshooting

### Common Issues

**Database Connection Errors**
```python
# Check your connection settings
try:
    pipeline.storage.test_connection()
    print("Database connection successful")
except Exception as e:
    print(f"Connection failed: {e}")
    # Check your .env file and database status
```

**Model Loading Issues**
```python
# Test model initialization
try:
    embeddings = pipeline.embed_generator.embed_text("test")
    print(f"Model working, embedding dimension: {len(embeddings)}")
except Exception as e:
    print(f"Model error: {e}")
    # Check API keys or model availability
```

**Performance Optimization**
- Use appropriate chunk sizes (256-512 tokens work well)
- Consider batch processing for large datasets
- Monitor vector index performance for large collections

### Logging and Debugging

Enable detailed logging for troubleshooting:

```python
import logging
logging.getLogger("clarifai_shared.embedding").setLevel(logging.DEBUG)
```

## API Reference Examples

The following examples show additional ways to use the embedding system API:

### Processing Tier 1 Content Directly

For complete Tier 1 Markdown files with metadata:

```python
# Process full Tier 1 Markdown content with embedded metadata
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
    print(f"Processing statistics: {result.metrics}")
else:
    print(f"Processing failed: {result.errors}")
```

### Single Block Processing

For processing individual utterance blocks:

```python
# Process a single utterance block
result = pipeline.process_single_block(
    text="This is a single utterance to embed.",
    clarifai_block_id="blk_single123",
    replace_existing=True
)

print(f"Processed {result.total_chunks} chunks")
print(f"Generated embeddings: {result.embedding_count}")
```

### Pipeline Health Monitoring

Check the status of pipeline components:

```python
# Check pipeline component health
status = pipeline.get_pipeline_status()
print(f"Overall status: {status['overall_status']}")

for component, info in status['components'].items():
    print(f"{component}: {info['status']}")
    if info.get('error'):
        print(f"  Error: {info['error']}")
```

### Working with Individual Components

For advanced use cases, you can work with components separately:

```python
from clarifai_shared.embedding import UtteranceChunker, EmbeddingGenerator, ClarifAIVectorStore

# Use components individually for custom workflows
chunker = UtteranceChunker()
chunks = chunker.chunk_utterance_block("Text to chunk", "blk_test")

generator = EmbeddingGenerator()
embedded_chunks = generator.embed_chunks(chunks)

vector_store = ClarifAIVectorStore()
metrics = vector_store.store_embeddings(embedded_chunks)
print(f"Storage metrics: {metrics}")
```

### Advanced Error Handling

The embedding system implements comprehensive error handling patterns:

```python
# Graceful fallback handling
try:
    result = pipeline.process_utterance(content, clarifai_id)
    if not result.success:
        # Check specific error types
        for error in result.errors:
            if "connection" in str(error).lower():
                print("Database connection issue - will retry later")
            elif "model" in str(error).lower():
                print("Model loading issue - check configuration")
            else:
                print(f"Processing error: {error}")
except Exception as e:
    # Unexpected errors are caught and logged
    logger.error(f"Unexpected error processing {clarifai_id}: {e}")
```

### Performance Optimization Techniques

**Batch Processing for Large Datasets**

```python
# Process multiple utterances efficiently
from pathlib import Path

def batch_process_vault(vault_path: str, batch_size: int = 10):
    """Process vault files in batches for better performance."""
    files = list(Path(vault_path).glob("**/*_tier1.md"))
    
    for i in range(0, len(files), batch_size):
        batch = files[i:i + batch_size]
        
        # Process batch concurrently
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            for file_path in batch:
                future = executor.submit(process_single_file, file_path)
                futures.append(future)
            
            # Collect results
            for future in futures:
                try:
                    result = future.result(timeout=30)
                    print(f"Processed: {result}")
                except Exception as e:
                    print(f"Batch processing error: {e}")
```

**Device Selection and Memory Management**

```python
# Configure for optimal performance
config_updates = {
    "embedding": {
        "device": "cuda" if torch.cuda.is_available() else "cpu",
        "batch_size": 16 if torch.cuda.is_available() else 4,
    }
}

pipeline = EmbeddingPipeline(config_override=config_updates)
```

## Complete Configuration Reference

### Full Configuration Example

Here's a complete configuration template for `settings/clarifai.config.yaml`:

```yaml
# Embedding system configuration
embedding:
  # Model configuration
  models:
    default: "sentence-transformers/all-MiniLM-L6-v2"
  
  # Processing settings
  device: "auto"              # "auto", "cpu", "cuda", "mps"
  batch_size: 32              # Chunks to process at once
  
  # PGVector settings
  pgvector:
    collection_name: "utterances"
    embed_dim: 384             # Must match model output dimension
    index_type: "ivfflat"      # Vector index type
    index_lists: 100           # Number of index lists
  
  # Chunking configuration
  chunking:
    chunk_size: 300            # Maximum tokens per chunk
    chunk_overlap: 30          # Token overlap between chunks
    keep_separator: true       # Preserve sentence separators
    merge_colon_endings: true  # Merge "text:" + continuation
    merge_short_prefixes: true # Merge fragments < min_chunk_tokens
    min_chunk_tokens: 5        # Minimum tokens per chunk

# Database configuration
databases:
  postgres:
    host: "postgres"           # Database host
    port: 5432                 # Database port
    database: "clarifai"       # Database name
    # User and password loaded from environment:
    # POSTGRES_USER, POSTGRES_PASSWORD
```

### Required Environment Variables

Create a `.env` file with these required variables:

```bash
# Database credentials (required)
POSTGRES_USER=clarifai
POSTGRES_PASSWORD=your_secure_password

# Optional database overrides
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=clarifai

# API keys (if using external embedding providers)
OPENAI_API_KEY=your_openai_key
```

### Performance Configuration Options

**Batch Processing Settings**

```yaml
embedding:
  batch_size: 32              # Chunks to process at once
  device: "auto"              # "auto", "cpu", "cuda", "mps"
```

**Vector Index Optimization**

```yaml
embedding:
  pgvector:
    index_type: "ivfflat"     # Vector index type for query performance
    index_lists: 100          # Number of index lists (adjust based on data size)
```

**Memory and Device Management**

```yaml
embedding:
  device: "auto"              # Automatically selects best available device
  # Options: "cpu", "cuda", "mps", "auto"
```

## Metadata Schema Reference

Each embedded chunk stores comprehensive metadata for tracking and analysis:

```python
# Complete metadata structure for each stored chunk
metadata_schema = {
    # Core identifiers
    "clarifai_id": "conv_001",                    # Original utterance ID
    "chunk_index": 0,                             # Position in original content
    
    # Content information
    "original_length": 1250,                      # Length of source content in characters
    "chunk_tokens": 128,                          # Estimated tokens in this chunk
    "original_text": "Full original text...",    # Complete source text for reference
    
    # Processing metadata
    "processing_timestamp": "2024-01-15T10:30:00Z",
    "model_name": "all-MiniLM-L6-v2",           # Embedding model used
    "embedding_dim": 384,                        # Vector dimension
    
    # Custom metadata (user-provided)
    "source": "demo",
    "type": "conversation",
    "tags": ["machine-learning", "tutorial"]
}
```

## Error Handling and Resilience Patterns

### Comprehensive Error Detection

```python
# The system provides detailed error information
try:
    result = pipeline.process_utterance(content, clarifai_id)
    
    # Check processing results
    if result.success:
        print(f"Successfully processed {result.stored_chunks} chunks")
        print(f"Processing metrics: {result.metrics}")
    else:
        # Handle different error types
        for error in result.errors:
            error_type = type(error).__name__
            
            if "ConnectionError" in error_type:
                print(f"Database connection issue: {error}")
                # Implement retry logic or fallback
                
            elif "ModelError" in error_type:
                print(f"Embedding model issue: {error}")
                # Check configuration or try different model
                
            elif "ValidationError" in error_type:
                print(f"Data validation issue: {error}")
                # Check input format or content
                
            else:
                print(f"General processing error: {error}")
                
except Exception as e:
    # Unexpected errors
    logger.error(f"Unexpected error: {e}", exc_info=True)
```

### Retry Logic and Graceful Fallbacks

```python
import time
from typing import Optional

def process_with_retry(
    pipeline: EmbeddingPipeline, 
    content: str, 
    clarifai_id: str,
    max_retries: int = 3,
    backoff_factor: float = 2.0
) -> Optional[ProcessingResult]:
    """Process content with exponential backoff retry."""
    
    for attempt in range(max_retries):
        try:
            result = pipeline.process_utterance(content, clarifai_id)
            
            if result.success:
                return result
            else:
                # Check if errors are retryable
                retryable_errors = ["ConnectionError", "TimeoutError", "TemporaryError"]
                if any(error_type in str(result.errors) for error_type in retryable_errors):
                    if attempt < max_retries - 1:
                        wait_time = backoff_factor ** attempt
                        print(f"Retryable error, waiting {wait_time}s before retry {attempt + 1}")
                        time.sleep(wait_time)
                        continue
                
                # Non-retryable errors or max retries reached
                print(f"Processing failed permanently: {result.errors}")
                return result
                
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = backoff_factor ** attempt
                print(f"Exception occurred, retrying in {wait_time}s: {e}")
                time.sleep(wait_time)
            else:
                print(f"Max retries exceeded: {e}")
                return None
    
    return None
```

## Next Steps

- Explore the [Embedding System Architecture](../components/embedding_system.md) for deeper technical details
- Check out the [Vector Store Documentation](../arch/on-vector_stores.md) for storage optimization
- See [Configuration Guide](../arch/design_config_panel.md) for advanced settings
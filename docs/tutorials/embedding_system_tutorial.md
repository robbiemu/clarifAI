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

## Next Steps

- Explore the [Embedding System Architecture](../components/embedding_system.md) for deeper technical details
- Check out the [Vector Store Documentation](../arch/on-vector_stores.md) for storage optimization
- See [Configuration Guide](../arch/design_config_panel.md) for advanced settings
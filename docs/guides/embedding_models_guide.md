# Embedding Models Guide

This document describes the embedding model system for aclarai's semantic vector generation functionality, providing configurable support for multiple embedding providers.

## Overview

The embedding models system enables aclarai to generate semantic vector representations of text content using various provider backends. It supports multiple embedding providers through a unified interface, allowing flexible model selection based on performance requirements, cost considerations, and deployment constraints.

## Architecture

### Embedding Model Components

The embedding system consists of several key components in the `aclarai_shared.embedding` package:

#### 1. Embedding Interface (`models.py`)
- `EmbeddingGenerator` main class for generating embeddings
- Provider-specific implementations (OpenAI, HuggingFace, SentenceTransformers)
- Configuration-driven model selection
- Automatic model caching and optimization

#### 2. Model Configuration
- Centralized configuration via `settings/aclarai.config.yaml`
- Environment variable overrides for API keys
- Per-model parameter customization
- Fallback model selection

#### 3. Provider Support
- **OpenAI**: `text-embedding-ada-002`, `text-embedding-3-small`, `text-embedding-3-large`
- **HuggingFace**: Any model from the Hub with embedding capabilities
- **SentenceTransformers**: Optimized local models for efficient inference

## Usage

### Basic Usage

```python
from aclarai_shared.embedding.models import EmbeddingGenerator
from aclarai_shared.config import load_config

# Load configuration
config = load_config()

# Initialize the embedding generator
embedder = EmbeddingGenerator(config)

# Generate embeddings for text
text = "Machine learning enables computers to learn patterns from data."
embedding = embedder.embed_text(text)

print(f"Generated embedding with {len(embedding)} dimensions")
```

### Batch Processing

For processing multiple texts efficiently:

```python
texts = [
    "Natural language processing enables text understanding.",
    "Computer vision helps machines interpret visual information.",
    "Deep learning uses neural networks for complex pattern recognition."
]

# Generate embeddings for multiple texts
embeddings = embedder.embed_batch(texts)

print(f"Generated {len(embeddings)} embeddings")
for i, emb in enumerate(embeddings):
    print(f"Text {i+1}: {len(emb)} dimensions")
```

## Configuration

### Model Selection

Configure your preferred embedding model in `settings/aclarai.config.yaml`:

```yaml
embedding:
  model:
    provider: "sentence_transformers"  # Options: openai, huggingface, sentence_transformers
    model_name: "all-MiniLM-L6-v2"   # Provider-specific model identifier
    max_length: 512                   # Maximum input length in tokens
    normalize_embeddings: true        # L2 normalize output vectors
    batch_size: 32                    # Batch size for processing
```

### Provider-Specific Configuration

#### OpenAI Models

```yaml
embedding:
  model:
    provider: "openai"
    model_name: "text-embedding-3-small"  # or text-embedding-ada-002, text-embedding-3-large
    max_length: 8192
    normalize_embeddings: true
    
# Environment variable required: OPENAI_API_KEY
```

**Available OpenAI Models:**
- `text-embedding-ada-002`: Legacy model, 1536 dimensions
- `text-embedding-3-small`: New efficient model, 1536 dimensions
- `text-embedding-3-large`: High-performance model, 3072 dimensions

#### HuggingFace Models

```yaml
embedding:
  model:
    provider: "huggingface"
    model_name: "sentence-transformers/all-mpnet-base-v2"
    max_length: 384
    normalize_embeddings: true
    device: "auto"  # auto, cpu, cuda, mps
```

**Popular HuggingFace Models:**
- `sentence-transformers/all-mpnet-base-v2`: High quality, 768 dimensions
- `sentence-transformers/all-MiniLM-L12-v2`: Balanced performance, 384 dimensions
- `sentence-transformers/multi-qa-mpnet-base-dot-v1`: Optimized for Q&A

#### SentenceTransformers Models

```yaml
embedding:
  model:
    provider: "sentence_transformers"
    model_name: "all-MiniLM-L6-v2"
    max_length: 256
    normalize_embeddings: true
    device: "auto"
    trust_remote_code: false
```

**Popular SentenceTransformers Models:**
- `all-MiniLM-L6-v2`: Fast and efficient, 384 dimensions
- `all-MiniLM-L12-v2`: Better quality, 384 dimensions
- `paraphrase-mpnet-base-v2`: High quality paraphrase detection

## Advanced Configuration

### Performance Optimization

```yaml
embedding:
  model:
    # Batch processing settings
    batch_size: 32              # Adjust based on GPU memory
    max_workers: 4              # Parallel processing threads
    
    # Caching settings
    cache_embeddings: true      # Cache computed embeddings
    cache_size: 1000           # Maximum cached embeddings
    
    # Memory management
    device: "auto"             # Automatic device selection
    precision: "float32"       # float32, float16, bfloat16
```

### Model Fallback Configuration

Configure fallback models for reliability:

```yaml
embedding:
  model:
    provider: "sentence_transformers"
    model_name: "all-MiniLM-L6-v2"
    
    # Fallback configuration
    fallback_models:
      - provider: "huggingface"
        model_name: "sentence-transformers/all-MiniLM-L12-v2"
      - provider: "openai"
        model_name: "text-embedding-3-small"
```

## Implementation Details

### Adding New Providers

To add support for a new embedding provider:

1. **Create Provider Class**: Implement the embedding interface
```python
class CustomEmbeddingProvider:
    def __init__(self, config: EmbeddingConfig):
        self.config = config
        # Initialize your provider
    
    def embed_text(self, text: str) -> List[float]:
        # Implement text embedding logic
        pass
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        # Implement batch embedding logic
        pass
```

2. **Register Provider**: Add to the provider registry
```python
# In models.py
EMBEDDING_PROVIDERS = {
    "openai": OpenAIEmbeddingProvider,
    "huggingface": HuggingFaceEmbeddingProvider,
    "sentence_transformers": SentenceTransformersEmbeddingProvider,
    "custom": CustomEmbeddingProvider,  # Add your provider
}
```

3. **Update Configuration Schema**: Add provider-specific options

### Error Handling

The embedding system implements robust error handling:

```python
try:
    embeddings = embedder.embed_text("Some text")
except EmbeddingError as e:
    # Handle embedding-specific errors
    logger.error(f"Embedding failed: {e}")
except ModelNotAvailableError as e:
    # Handle model loading errors
    logger.error(f"Model unavailable: {e}")
    # Attempt fallback model
```

### Monitoring and Logging

Embedding operations are logged with structured context:

```python
# Logging includes:
# - service: "aclarai-core"  
# - filename.function_name: "models.embed_text"
# - model_name: "all-MiniLM-L6-v2"
# - text_length: 156
# - embedding_dimension: 384
# - processing_time_ms: 45
```

## Model Selection Guidelines

### Performance vs Quality Trade-offs

| Model Type | Speed | Quality | Memory | Use Case |
|------------|-------|---------|--------|----------|
| MiniLM-L6-v2 | Fast | Good | Low | Real-time applications |
| MiniLM-L12-v2 | Medium | Better | Medium | Balanced performance |
| MPNet-base-v2 | Slow | Best | High | Offline processing |
| OpenAI-3-small | Fast* | Good | None** | API-based applications |

*Speed depends on API latency  
**No local memory usage

### Deployment Considerations

**Local Deployment:**
- Use SentenceTransformers for full control
- Consider model size vs performance trade-offs
- Optimize for your specific hardware

**Cloud Deployment:**
- OpenAI for minimal infrastructure
- HuggingFace Inference API for compromise
- Local models for data privacy

**Edge Deployment:**
- Quantized models for reduced memory
- ONNX runtime for optimized inference
- Consider TensorFlow Lite variants

## Troubleshooting

### Common Issues

**Model Loading Errors:**
```bash
# Check model availability
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
```

**API Authentication:**
```bash
# Verify OpenAI API key
export OPENAI_API_KEY=your_key_here
python -c "import openai; print(openai.models.list())"
```

**Memory Issues:**
```yaml
# Reduce batch size or switch to smaller model
embedding:
  model:
    batch_size: 8  # Reduce from default 32
    model_name: "all-MiniLM-L6-v2"  # Switch to smaller model
```

**Performance Optimization:**
```yaml
# Enable GPU acceleration
embedding:
  model:
    device: "cuda"  # Use GPU if available
    precision: "float16"  # Reduce memory usage
```

## Next Steps

- Explore the [Embedding System Tutorial](../tutorials/embedding_system_tutorial.md) for hands-on examples
- Check the [Vector Store Documentation](../arch/on-vector_stores.md) for storage integration
- See the [Configuration Guide](../arch/design_config_panel.md) for advanced settings
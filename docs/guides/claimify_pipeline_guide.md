# Claimify Pipeline Configuration and Usage Guide

This guide demonstrates how to configure and use the Claimify pipeline to extract high-quality claims from text content.

## Overview

The Claimify pipeline processes text through three stages (Selection → Disambiguation → Decomposition) to extract atomic, self-contained, and verifiable claims. This guide covers basic setup, configuration, and usage patterns.

## Prerequisites

- ClarifAI development environment set up
- Configuration file `settings/clarifai.config.yaml` properly configured
- LLM access configured (OpenAI, Azure OpenAI, or local models)

## Basic Configuration

### 1. Pipeline Configuration

The pipeline is configured through the main configuration file:

```yaml
claimify:
  context_window:
    p: 3  # Previous sentences for context
    f: 1  # Following sentences for context
  models:
    selection: null      # Uses default if not specified
    disambiguation: null 
    decomposition: null
    default: "gpt-3.5-turbo"
  processing:
    max_retries: 3
    timeout_seconds: 30
    temperature: 0.1
  thresholds:
    selection_confidence: 0.5
    disambiguation_confidence: 0.5
    decomposition_confidence: 0.5
```

### 2. Creating Pipeline Instance

```python
from clarifai_shared.claimify import (
    ClaimifyPipeline,
    load_claimify_config_from_file
)

# Load configuration
config = load_claimify_config_from_file("settings/clarifai.config.yaml")

# Create pipeline
pipeline = ClaimifyPipeline(config=config)
```

## Processing Sentences

### 1. Basic Sentence Processing

```python
from clarifai_shared.claimify import SentenceChunk, ClaimifyContext

# Create sentence chunks
sentences = [
    SentenceChunk(
        text="The user submitted a request to the API endpoint.",
        source_id="doc_001",
        chunk_id="chunk_001",
        sentence_index=0
    ),
    SentenceChunk(
        text='The system returned an error: "Invalid parameter type".',
        source_id="doc_001", 
        chunk_id="chunk_002",
        sentence_index=1
    ),
    SentenceChunk(
        text="This caused the request to fail completely.",
        source_id="doc_001",
        chunk_id="chunk_003", 
        sentence_index=2
    )
]

# Process sentences with context
for i, sentence in enumerate(sentences):
    # Build context window
    context = ClaimifyContext(
        current_sentence=sentence,
        preceding_sentences=sentences[max(0, i-config.context_window_p):i],
        following_sentences=sentences[i+1:i+1+config.context_window_f]
    )
    
    # Process through pipeline
    result = pipeline.process(context)
    
    # Check results
    if result.was_processed:
        print(f"✅ Processed: {sentence.text}")
        print(f"   Claims: {len(result.final_claims)}")
        print(f"   Sentences: {len(result.final_sentences)}")
    else:
        print(f"❌ Skipped: {sentence.text}")
```

### 2. Batch Processing

```python
# Process multiple sentences in batch
contexts = []
for i, sentence in enumerate(sentences):
    context = ClaimifyContext(
        current_sentence=sentence,
        preceding_sentences=sentences[max(0, i-config.context_window_p):i],
        following_sentences=sentences[i+1:i+1+config.context_window_f]
    )
    contexts.append(context)

# Process all contexts
results = []
for context in contexts:
    result = pipeline.process(context)
    results.append(result)

# Analyze batch results
total_claims = sum(len(r.final_claims) for r in results)
total_sentences = sum(len(r.final_sentences) for r in results)
processed_count = sum(1 for r in results if r.was_processed)

print(f"Batch Results:")
print(f"- Processed: {processed_count}/{len(results)} sentences")
print(f"- Claims extracted: {total_claims}")
print(f"- Sentences created: {total_sentences}")
```

## Configuration Options

### Context Window Tuning

Adjust context window size based on your content:

```yaml
claimify:
  context_window:
    p: 5  # More preceding context for complex topics
    f: 2  # More following context for better disambiguation
```

### Model Selection

Configure different models per stage:

```yaml
claimify:
  models:
    selection: "gpt-4"           # Use more powerful model for selection
    disambiguation: "gpt-3.5-turbo"  # Standard model for disambiguation
    decomposition: "gpt-4"       # More powerful model for decomposition
    default: "gpt-3.5-turbo"
```

### Processing Parameters

Fine-tune processing behavior:

```yaml
claimify:
  processing:
    max_retries: 5         # More retries for unreliable connections
    timeout_seconds: 60    # Longer timeout for complex processing
    temperature: 0.0       # More deterministic results
```

## Quality Control

### Understanding Claim Quality

Claims are evaluated on three criteria:

1. **Atomic**: Single, indivisible fact
2. **Self-contained**: No ambiguous references (pronouns, unclear terms)
3. **Verifiable**: Contains factual, checkable information

### Quality Assessment

```python
# Check individual claim quality
for result in results:
    for claim in result.final_claims:
        print(f"Claim: {claim.text}")
        print(f"- Atomic: {claim.is_atomic}")
        print(f"- Self-contained: {claim.is_self_contained}")
        print(f"- Verifiable: {claim.is_verifiable}")
        print(f"- Overall quality: {'✅ Valid' if claim.passes_criteria else '❌ Invalid'}")
```

### Pipeline Statistics

```python
# Get pipeline statistics
stats = pipeline.get_statistics()
print(f"Pipeline Performance:")
print(f"- Selection rate: {stats['selection_rate']:.1%}")
print(f"- Average claims per sentence: {stats['claims_per_sentence']:.2f}")
print(f"- Processing time: {stats['avg_processing_time']:.3f}s")
```

## Error Handling

### Graceful Degradation

```python
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    result = pipeline.process(context)
    if result.errors:
        logger.warning(f"Processing completed with errors: {result.errors}")
except Exception as e:
    logger.error(f"Pipeline processing failed: {e}")
    # Handle failure gracefully
```

### Monitoring Processing Issues

```python
# Check for common issues
problematic_sentences = []
for result in results:
    if not result.was_processed:
        problematic_sentences.append({
            'text': result.original_chunk.text,
            'reason': 'Not selected by Selection agent'
        })
    elif result.errors:
        problematic_sentences.append({
            'text': result.original_chunk.text,
            'reason': '; '.join(result.errors)
        })

if problematic_sentences:
    print("⚠️ Sentences requiring attention:")
    for sentence in problematic_sentences:
        print(f"- {sentence['text'][:50]}... ({sentence['reason']})")
```

## Advanced Usage

### Custom Model Integration

```python
from llama_index.llms.openai import OpenAI

# Create custom LLM instances
selection_llm = OpenAI(model="gpt-4", temperature=0.0)
decomposition_llm = OpenAI(model="gpt-4", temperature=0.1)

# Create pipeline with custom models
pipeline = ClaimifyPipeline(
    config=config,
    selection_llm=selection_llm,
    decomposition_llm=decomposition_llm
)
```

### Performance Optimization

```python
# Optimize for throughput
config.processing.timeout_seconds = 15  # Faster timeout
config.processing.max_retries = 1       # Fewer retries

# Optimize for quality  
config.processing.temperature = 0.0     # More deterministic
config.thresholds.selection_confidence = 0.7  # Higher selection threshold
```

## Next Steps

- **Integration**: See `docs/tutorials/claimify_integration_tutorial.md` for Neo4j integration
- **Advanced Configuration**: Review `docs/arch/on-claim_generation.md` for quality criteria details
- **LLM Configuration**: Check `docs/arch/on-llm_interaction_strategy.md` for model setup

## Troubleshooting

### Common Issues

1. **Low Selection Rates**: Adjust selection confidence threshold or review content quality
2. **Poor Claim Quality**: Increase context window size or use more powerful models
3. **Timeout Errors**: Increase timeout duration or reduce batch size
4. **Memory Issues**: Process sentences in smaller batches

### Performance Monitoring

```python
# Monitor processing performance
import time

start_time = time.time()
results = [pipeline.process(context) for context in contexts]
total_time = time.time() - start_time

print(f"Performance Metrics:")
print(f"- Total processing time: {total_time:.2f}s")
print(f"- Sentences per second: {len(contexts)/total_time:.2f}")
print(f"- Average time per sentence: {total_time/len(contexts):.3f}s")
```
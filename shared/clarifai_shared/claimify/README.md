# Claimify Pipeline Architecture

## Overview

The Claimify pipeline implements the core claim extraction functionality for ClarifAI, processing sentence chunks through three sequential stages to extract high-quality, atomic claims from Tier 1 content.

## Architecture

### Pipeline Stages

The pipeline follows the architecture described in `docs/arch/on-claim_generation.md`:

1. **Selection** - Identifies sentence chunks containing verifiable information
2. **Disambiguation** - Rewrites sentences to remove ambiguities and add context  
3. **Decomposition** - Breaks sentences into atomic, self-contained claims

### Core Components

#### Data Models (`data_models.py`)

- **`SentenceChunk`** - Input unit representing a sentence from Tier 1 content
- **`ClaimifyContext`** - Context window with preceding/following sentences (p, f parameters)
- **`ClaimCandidate`** - Potential claim with quality criteria (atomic, self-contained, verifiable)
- **`ClaimifyResult`** - Complete processing result for a sentence
- **`ClaimifyConfig`** - Pipeline configuration including model settings and thresholds

#### Agents (`agents.py`)

- **`SelectionAgent`** - Implements selection logic with heuristic and LLM-based approaches
- **`DisambiguationAgent`** - Handles pronoun resolution and context addition
- **`DecompositionAgent`** - Extracts atomic claims and applies quality criteria

#### Pipeline Orchestrator (`pipeline.py`)

- **`ClaimifyPipeline`** - Main orchestrator coordinating all three stages
- Context window management
- Error handling and logging
- Performance statistics

## Key Features

### Model Injection Support

The pipeline supports injecting different LLM instances for each stage:

```python
pipeline = ClaimifyPipeline(
    config=config,
    selection_llm=selection_model,
    disambiguation_llm=disambiguation_model,
    decomposition_llm=decomposition_model
)
```

### Context Window Processing

Configurable context window with preceding (`p`) and following (`f`) sentences:

```python
config = ClaimifyConfig(
    context_window_p=3,  # 3 preceding sentences
    context_window_f=1   # 1 following sentence
)
```

### Quality Criteria Evaluation

Claims are evaluated against three criteria:
- **Atomic** - Single, indivisible fact
- **Self-contained** - No ambiguous references
- **Verifiable** - Contains factual, checkable information

### Structured Output

Processing results are structured for integration with the knowledge graph:
- Valid claims → `:Claim` nodes
- Invalid claims → `:Sentence` nodes

### Comprehensive Logging

Detailed logging throughout the pipeline:
- Stage decisions and reasoning
- Transformations and changes made
- Timing and performance metrics
- Error handling and recovery

## Configuration

### Model Selection

Models can be configured per stage or use fallback defaults:

```yaml
model:
  claimify:
    selection: "gpt-4"
    disambiguation: "claude-3-opus"  
    decomposition: "gpt-4"
    default: "gpt-3.5-turbo"
```

### Quality Thresholds

Configurable confidence thresholds for each stage:

```python
config = ClaimifyConfig(
    selection_confidence_threshold=0.7,
    disambiguation_confidence_threshold=0.6,
    decomposition_confidence_threshold=0.8
)
```

### Processing Parameters

```python
config = ClaimifyConfig(
    max_retries=3,
    timeout_seconds=30,
    temperature=0.1,
    max_tokens=1000
)
```

## Usage Examples

### Basic Processing

```python
from clarifai_shared.claimify import ClaimifyPipeline, SentenceChunk, ClaimifyConfig

# Configure pipeline
config = ClaimifyConfig(context_window_p=2, context_window_f=1)
pipeline = ClaimifyPipeline(config=config)

# Create sentence chunks
sentences = [
    SentenceChunk(
        text="The system reported an error.",
        source_id="blk_001",
        chunk_id="chunk_001", 
        sentence_index=0
    )
]

# Process sentences
results = pipeline.process_sentences(sentences)

# Access results
for result in results:
    if result.was_processed:
        claims = result.final_claims
        sentence_nodes = result.final_sentences
```

### With LLM Integration

```python
# When LLMs are available
pipeline = ClaimifyPipeline(
    config=config,
    selection_llm=my_selection_llm,
    disambiguation_llm=my_disambiguation_llm,
    decomposition_llm=my_decomposition_llm
)
```

## Error Handling

The pipeline implements robust error handling:

- **Stage-level fallbacks** - LLM failures fall back to heuristics
- **Graceful degradation** - Partial results returned on errors
- **Comprehensive logging** - All errors captured with context
- **Retry logic** - Configurable retry attempts with backoff

## Performance

### Timing Metrics

The pipeline tracks processing time for:
- Individual stage processing
- Total sentence processing time
- Average times across batch processing

### Statistics

Comprehensive statistics provided:
- Selection rates
- Claim extraction rates  
- Error counts
- Processing throughput

## Testing

Comprehensive test suite covering:

### Unit Tests
- `test_data_models.py` - Data structure validation
- `test_agents.py` - Individual agent functionality
- `test_pipeline.py` - Pipeline orchestration and integration

### Test Coverage
- Happy path processing
- Error handling scenarios
- Edge cases (empty text, questions, compound sentences)
- Configuration variations
- Performance testing

### Integration Tests
- End-to-end claim extraction
- Multi-sentence processing with context
- Real-world content examples

## Integration Points

### Input Sources
- Tier 1 markdown files via existing embedding pipeline
- Sentence chunks from utterance chunking system

### Output Destinations  
- Knowledge graph (Neo4j) as `:Claim` and `:Sentence` nodes
- Evaluation agents for quality scoring
- Concept linking for relationship extraction

### Configuration Integration
- Central YAML configuration system
- LLM provider abstraction layer
- Logging framework integration

## Future Enhancements

### Planned Improvements
- Advanced LLM prompt engineering
- Claim quality scoring integration
- Batch processing optimizations
- Caching for repeated content
- Multi-language support

### Extension Points
- Custom quality criteria plugins
- Alternative decomposition strategies
- Domain-specific heuristics
- Real-time processing modes

## Dependencies

### Required
- Python 3.11+
- Standard library (dataclasses, logging, time, typing)

### Optional
- LLM providers (OpenAI, Anthropic, etc.) for enhanced processing
- YAML configuration support
- Structured logging frameworks

The implementation prioritizes minimal dependencies and graceful fallbacks to ensure robust operation even with limited external resources.
# aclarai Claimify Pipeline System Documentation

This document provides comprehensive documentation for the aclarai Claimify pipeline system, which extracts high-quality claims from Tier 1 content through a three-stage process.

## Overview

The Claimify pipeline processes sentence chunks through three sequential stages to extract atomic, self-contained, and verifiable claims:

1. **Selection** - Identifies sentence chunks containing verifiable information
2. **Disambiguation** - Rewrites sentences to remove ambiguities and add context  
3. **Decomposition** - Breaks sentences into atomic, self-contained claims

## Architecture

The system follows the aclarai architecture principles:

- **Configuration-driven**: All parameters configurable via `settings/aclarai.config.yaml`
- **LlamaIndex-first**: Uses LlamaIndex abstractions for LLM integration
- **Reusable**: Placed in shared library for cross-service usage
- **Resilient**: Graceful error handling and fallbacks
- **Logged**: Structured logging with service context

## Components

### 1. Pipeline Orchestrator

**`ClaimifyPipeline`** - Main orchestrator coordinating all three stages with context window management, error handling, and performance statistics.

**Key Features:**
- Context window management (configurable p=3 preceding, f=1 following sentences)
- Model injection architecture supporting different LLMs per stage
- Comprehensive error handling and recovery
- Performance metrics and timing analysis
- Structured logging following `docs/arch/idea-logging.md`

### 2. Processing Agents

#### SelectionAgent
Identifies sentence chunks that contain verifiable, factual information suitable for claim extraction.

**Responsibilities:**
- Evaluate sentences for factual content
- Apply verifiability criteria
- Provide confidence scores and reasoning
- Log selection decisions

#### DisambiguationAgent  
Rewrites selected sentences to resolve pronouns and add missing context.

**Responsibilities:**
- Resolve ambiguous pronouns (e.g., "It failed" → "The system failed")
- Add inferred subjects and context
- Maintain semantic meaning while improving clarity
- Track changes made during disambiguation

#### DecompositionAgent
Breaks disambiguated sentences into atomic, self-contained claims.

**Responsibilities:**
- Extract individual factual statements
- Apply quality criteria (atomic, self-contained, verifiable)
- Generate claim candidates with quality assessments
- Provide reasoning for acceptance/rejection

### 3. Data Models

#### Core Processing Types
- **`SentenceChunk`** - Input unit representing a sentence from Tier 1 content
- **`ClaimifyContext`** - Context window with preceding/following sentences
- **`ClaimCandidate`** - Potential claim with quality criteria evaluation
- **`ClaimifyResult`** - Complete processing result for a sentence

#### Configuration
- **`ClaimifyConfig`** - Pipeline configuration including model settings, thresholds, and processing parameters

#### Results
- **`SelectionResult`** - Selection stage output with decision and reasoning
- **`DisambiguationResult`** - Disambiguation stage output with changes made
- **`DecompositionResult`** - Decomposition stage output with claim candidates

## Integration Points

### Configuration System
The pipeline integrates with the main aclarai configuration through `config_integration.py`:

```yaml
claimify:
  context_window:
    p: 3  # Previous sentences
    f: 1  # Following sentences
  models:
    selection: null      # Uses default if not specified
    disambiguation: null 
    decomposition: null
    default: "gpt-3.5-turbo"
  processing:
    max_retries: 3
    timeout_seconds: 30
    temperature: 0.1
```

### Neo4j Graph Storage
Claims and sentences are persisted to the knowledge graph through the integration layer:

- Valid claims → `:Claim` nodes ready for evaluation scoring
- Invalid claims → `:Sentence` nodes preserved for concept linking
- `ORIGINATES_FROM` relationships connecting to source `:Block` nodes

### LLM Integration
Supports model injection for each stage with fallback to configured defaults. Prompt templates follow `docs/arch/on-llm_interaction_strategy.md`.

## Quality Criteria

Claims are evaluated against three criteria from `docs/arch/on-claim_generation.md`:

- **Atomic**: Single, indivisible fact
- **Self-contained**: No ambiguous references  
- **Verifiable**: Contains factual, checkable information

Only claims meeting all criteria become `:Claim` nodes; others become `:Sentence` nodes.

## Error Handling

The system implements resilient error handling:

- LLM timeouts and retries with exponential backoff
- Graceful degradation when processing fails
- Comprehensive error logging with context
- Pipeline statistics tracking success/failure rates

## Performance Monitoring

The pipeline provides detailed statistics:

- Selection rates and processing throughput
- Claim extraction ratios and quality metrics  
- Stage-by-stage timing analysis
- Comprehensive error tracking

## Usage Examples

For practical usage examples and tutorials, see:
- **Configuration & Usage**: `docs/guides/claimify_pipeline_guide.md` - Configuration and basic usage patterns
- **Integration Tutorial**: `docs/tutorials/claimify_integration_tutorial.md` - End-to-end integration with Neo4j

## References

- `docs/arch/on-claim_generation.md` - Claim quality criteria and pipeline design
- `docs/arch/on-llm_interaction_strategy.md` - LLM integration patterns
- `docs/arch/idea-logging.md` - Structured logging requirements
- `docs/arch/on-neo4j_interaction.md` - Graph storage patterns
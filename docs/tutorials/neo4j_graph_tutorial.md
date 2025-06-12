# Neo4j Graph Management Tutorial

This tutorial shows you how to use the ClarifAI Neo4j graph system to create and manage (:Claim) and (:Sentence) nodes in your knowledge graph. We'll walk through everything from basic data models to real-world integration patterns.

## What You'll Learn

- How to create and use ClaimInput and SentenceInput objects
- How to connect to Neo4j and set up the schema
- How to create Claims and Sentences in batch
- How to integrate with the Claimify pipeline
- Best practices for quality filtering and error handling

## Prerequisites

Before starting this tutorial, make sure you have:
- A running Neo4j database
- ClarifAI shared library installed
- Neo4j connection credentials (NEO4J_HOST, NEO4J_USER, NEO4J_PASSWORD)

## Part 1: Understanding the Data Models

Let's start by exploring the data models that represent Claims and Sentences.

### Creating ClaimInput Objects

ClaimInput objects represent claims that will be stored in the knowledge graph. They contain the claim text, evaluation scores from the Claimify pipeline, and metadata:

```python
from clarifai_shared.graph import ClaimInput

# Create a high-quality claim with all scores
claim_input = ClaimInput(
    text="Python is a programming language developed by Guido van Rossum",
    block_id="block_conversation_001_chunk_05",
    entailed_score=0.98,
    coverage_score=0.95,
    decontextualization_score=0.87
)

print(f"Claim ID: {claim_input.claim_id}")  # Auto-generated UUID
print(f"Text: {claim_input.text}")
print(f"Source: {claim_input.block_id}")
print(f"Scores: E={claim_input.entailed_score}, C={claim_input.coverage_score}, D={claim_input.decontextualization_score}")
```

### Handling Failed Evaluation Agents

In real systems, evaluation agents can fail. The ClaimInput model gracefully handles null scores:

```python
# Claim with a failed coverage agent
claim_with_null_score = ClaimInput(
    text="Machine learning algorithms require training data",
    block_id="block_conversation_001_chunk_12",
    entailed_score=0.92,
    coverage_score=None,  # Coverage agent failed
    decontextualization_score=0.94
)

print(f"Coverage score: {claim_with_null_score.coverage_score}")  # None
```

### Creating SentenceInput Objects

SentenceInput objects represent utterances that didn't produce high-quality claims but should still be stored:

```python
from clarifai_shared.graph import SentenceInput

# Ambiguous sentence that can't be verified
sentence_input = SentenceInput(
    text="Hmm, that's really interesting",
    block_id="block_conversation_001_chunk_08",
    ambiguous=True,
    verifiable=False
)

print(f"Sentence ID: {sentence_input.sentence_id}")  # Auto-generated UUID
print(f"Ambiguous: {sentence_input.ambiguous}")
print(f"Verifiable: {sentence_input.verifiable}")
```

### Converting to Full Objects

Input objects can be converted to full Claim and Sentence objects with metadata:

```python
from clarifai_shared.graph import Claim, Sentence

# Convert to full objects
claim = Claim.from_input(claim_input)
sentence = Sentence.from_input(sentence_input)

print(f"Claim version: {claim.version}")  # Starts at 1
print(f"Claim timestamp: {claim.timestamp}")  # ISO format datetime
print(f"Serializable: {claim.to_dict()}")  # Dictionary for Neo4j storage
```

## Part 2: Database Operations

Now let's connect to Neo4j and create nodes in the database.

### Setting Up the Connection

```python
from clarifai_shared.graph import Neo4jGraphManager
from clarifai_shared.config import ClarifAIConfig

# Load configuration (uses environment variables)
config = ClarifAIConfig.from_env()

# Create graph manager with context management for automatic cleanup
with Neo4jGraphManager(config) as graph:
    print("Connected to Neo4j successfully")
    
    # Setup schema (constraints and indexes)
    graph.setup_schema()
    print("Schema setup completed")
    
    # Database operations go here...
```

### Creating Claims in Batch

Batch operations are efficient for creating multiple nodes:

```python
# Prepare multiple claims
claim_inputs = [
    ClaimInput(
        text="Python is a programming language developed by Guido van Rossum",
        block_id="block_conversation_001_chunk_05",
        entailed_score=0.98,
        coverage_score=0.95,
        decontextualization_score=0.87
    ),
    ClaimInput(
        text="Machine learning algorithms require training data to learn patterns", 
        block_id="block_conversation_001_chunk_12",
        entailed_score=0.92,
        coverage_score=0.88,
        decontextualization_score=0.94
    ),
    ClaimInput(
        text="Neo4j is a graph database that stores data as nodes and relationships",
        block_id="block_conversation_001_chunk_18",
        entailed_score=0.96,
        coverage_score=0.91,
        decontextualization_score=0.89
    )
]

# Create all claims in a single batch operation
with Neo4jGraphManager(config) as graph:
    graph.setup_schema()
    claims = graph.create_claims(claim_inputs)
    print(f"Successfully created {len(claims)} Claim nodes")
    
    # Each claim now has ORIGINATES_FROM relationship to its Block node
```

### Creating Sentences in Batch

Similarly, create sentences for non-claim utterances:

```python
# Prepare sentences that didn't become claims
sentence_inputs = [
    SentenceInput(
        text="Hmm, that's really interesting to think about",
        block_id="block_conversation_001_chunk_08",
        ambiguous=True,
        verifiable=False
    ),
    SentenceInput(
        text="What do you think we should do next?",
        block_id="block_conversation_001_chunk_25",
        ambiguous=False,
        verifiable=False
    ),
    SentenceInput(
        text="This seems complex and has multiple interpretations",
        block_id="block_conversation_001_chunk_30", 
        ambiguous=True,
        verifiable=True
    )
]

# Create sentences in batch
with Neo4jGraphManager(config) as graph:
    sentences = graph.create_sentences(sentence_inputs)
    print(f"Successfully created {len(sentences)} Sentence nodes")
```

### Retrieving and Querying Nodes

Once created, you can retrieve nodes by ID:

```python
with Neo4jGraphManager(config) as graph:
    # Get a specific claim
    claim_data = graph.get_claim_by_id("claim_python_language")
    if claim_data:
        print(f"Found claim: '{claim_data['text']}'")
        print(f"Entailed score: {claim_data['entailed_score']}")
        print(f"Coverage score: {claim_data['coverage_score']}")
    
    # Get a specific sentence
    sentence_data = graph.get_sentence_by_id("sentence_hmm_interesting")
    if sentence_data:
        print(f"Found sentence: '{sentence_data['text']}'")
        print(f"Ambiguous: {sentence_data['ambiguous']}")
    
    # Get overall statistics
    counts = graph.count_nodes()
    print(f"Graph contains:")
    print(f"  Claims: {counts['claims']}")
    print(f"  Sentences: {counts['sentences']}")
    print(f"  Blocks: {counts['blocks']}")
```

## Part 3: Claimify Pipeline Integration

Here's how to integrate this system with the Claimify claim extraction pipeline.

### Processing Claimify Output

Simulate converting raw Claimify results into graph nodes:

```python
# Simulate raw output from Claimify pipeline
raw_claimify_results = [
    {
        "text": "The Earth orbits the Sun in an elliptical path",
        "source_block": "block_astro_conv_chunk_7",
        "evaluation_scores": {
            "entailed": 0.97,
            "coverage": 0.94,
            "decontextualization": 0.91
        }
    },
    {
        "text": "Neural networks learn through backpropagation",
        "source_block": "block_ml_conv_chunk_15",
        "evaluation_scores": {
            "entailed": 0.89,
            "coverage": 0.85,
            "decontextualization": 0.88
        }
    },
    {
        "text": "This system is efficient", 
        "source_block": "block_sys_conv_chunk_22",
        "evaluation_scores": {
            "entailed": 0.82,
            "coverage": None,  # Coverage agent failed
            "decontextualization": 0.45  # Low score
        }
    }
]

# Convert to ClaimInput objects with quality filtering
claim_inputs = []
filtered_claims = []

for result in raw_claimify_results:
    scores = result["evaluation_scores"]
    
    claim_input = ClaimInput(
        text=result["text"],
        block_id=result["source_block"],
        entailed_score=scores.get("entailed"),
        coverage_score=scores.get("coverage"),
        decontextualization_score=scores.get("decontextualization")
    )
    
    # Apply quality thresholds
    if claim_input.entailed_score and claim_input.entailed_score >= 0.85:
        if claim_input.decontextualization_score and claim_input.decontextualization_score >= 0.70:
            claim_inputs.append(claim_input)
            print(f"✓ High-quality claim: {claim_input.text[:40]}...")
        else:
            filtered_claims.append((claim_input, "Low decontextualization score"))
            print(f"✗ Filtered claim: {claim_input.text[:40]}... (low decontextualization)")
    else:
        filtered_claims.append((claim_input, "Low entailment score"))
        print(f"✗ Filtered claim: {claim_input.text[:40]}... (low entailment)")

print(f"\nResult: {len(claim_inputs)} high-quality claims, {len(filtered_claims)} filtered")
```

### Processing Non-Claim Sentences

Handle utterances that didn't produce claims:

```python
# Simulate raw sentences that didn't become claims
raw_sentence_results = [
    {
        "text": "Wow, I never thought about it that way",
        "source_block": "block_astro_conv_chunk_9",
        "analysis": {"ambiguous": True, "verifiable": False}
    },
    {
        "text": "Can you explain that again?",
        "source_block": "block_ml_conv_chunk_18", 
        "analysis": {"ambiguous": False, "verifiable": False}
    }
]

# Convert to SentenceInput objects
sentence_inputs = []
for result in raw_sentence_results:
    analysis = result["analysis"]
    
    sentence_input = SentenceInput(
        text=result["text"],
        block_id=result["source_block"],
        ambiguous=analysis.get("ambiguous"),
        verifiable=analysis.get("verifiable")
    )
    sentence_inputs.append(sentence_input)
    print(f"➤ Sentence: {sentence_input.text}")
```

### Complete Integration Example

Put it all together in a complete integration:

```python
def process_claimify_batch(raw_results, config):
    """Process a batch of Claimify results and create graph nodes."""
    
    with Neo4jGraphManager(config) as graph:
        # Ensure schema is ready
        graph.setup_schema()
        
        # Process claims with quality filtering
        claim_inputs = []
        sentence_inputs = []
        
        for result in raw_results:
            if result["type"] == "claim":
                scores = result["evaluation_scores"]
                claim_input = ClaimInput(
                    text=result["text"],
                    block_id=result["source_block"],
                    entailed_score=scores.get("entailed"),
                    coverage_score=scores.get("coverage"),
                    decontextualization_score=scores.get("decontextualization")
                )
                
                # Apply quality thresholds
                if (claim_input.entailed_score and claim_input.entailed_score >= 0.85 and
                    claim_input.decontextualization_score and claim_input.decontextualization_score >= 0.70):
                    claim_inputs.append(claim_input)
                else:
                    # Convert low-quality claims to sentences
                    sentence_input = SentenceInput(
                        text=result["text"],
                        block_id=result["source_block"],
                        ambiguous=True,  # Low-quality claims are ambiguous
                        verifiable=True   # But potentially verifiable
                    )
                    sentence_inputs.append(sentence_input)
                    
            elif result["type"] == "sentence":
                analysis = result["analysis"]
                sentence_input = SentenceInput(
                    text=result["text"],
                    block_id=result["source_block"],
                    ambiguous=analysis.get("ambiguous"),
                    verifiable=analysis.get("verifiable")
                )
                sentence_inputs.append(sentence_input)
        
        # Create nodes in batch
        claims = graph.create_claims(claim_inputs) if claim_inputs else []
        sentences = graph.create_sentences(sentence_inputs) if sentence_inputs else []
        
        return {
            "claims_created": len(claims),
            "sentences_created": len(sentences),
            "total_processed": len(raw_results)
        }

# Usage
config = ClarifAIConfig.from_env()
results = process_claimify_batch(your_claimify_results, config)
print(f"Processed {results['total_processed']} items: {results['claims_created']} claims, {results['sentences_created']} sentences")
```

## Part 4: Testing Without a Database

For development and testing, you can work with the data models without a database connection:

```python
def test_data_models_without_database():
    """Test the data models without requiring Neo4j."""
    
    # Create sample data
    claim_inputs = [
        ClaimInput(
            text="Python is a programming language",
            block_id="block123",
            entailed_score=0.95
        ),
        ClaimInput(
            text="Machine learning uses algorithms",
            block_id="block456",
            entailed_score=0.88,
            coverage_score=None  # Test null handling
        )
    ]
    
    # Convert to full objects
    claims = [Claim.from_input(ci) for ci in claim_inputs]
    
    # Verify properties
    for claim in claims:
        assert claim.claim_id is not None
        assert claim.version == 1
        assert claim.timestamp is not None
        assert isinstance(claim.to_dict(), dict)
        print(f"✓ Claim validated: {claim.text[:30]}...")
    
    print(f"Successfully validated {len(claims)} claims without database")

# Run the test
test_data_models_without_database()
```

## Troubleshooting

### Common Issues

**Connection Errors:**
```python
try:
    with Neo4jGraphManager(config) as graph:
        graph.setup_schema()
except Exception as e:
    print(f"Connection failed: {e}")
    print("Check NEO4J_HOST, NEO4J_USER, NEO4J_PASSWORD environment variables")
```

**Authentication Errors:**
- Verify NEO4J_USER and NEO4J_PASSWORD are correct
- Check that the user has write permissions

**Validation Errors:**
- Ensure all required fields are provided
- Check that block_id references exist in the graph

### Best Practices

1. **Always use context managers** for database connections
2. **Set up schema** before creating nodes
3. **Use batch operations** for efficiency
4. **Apply quality filtering** to maintain graph quality
5. **Handle null scores gracefully** for failed agents
6. **Test without database** during development

## Next Steps

Now that you understand the Neo4j graph system:

1. Integrate it into your Claimify pipeline
2. Set up quality thresholds based on your use case
3. Monitor graph growth and performance
4. Consider adding more sophisticated queries and analytics

For more details on the underlying implementation, see the [Graph System Components](../components/graph_system.md) documentation.
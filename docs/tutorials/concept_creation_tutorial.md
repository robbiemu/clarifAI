# Concept Creation Tutorial

This tutorial explains the end-to-end flow from text processing to the creation of `[[Concept]]` Markdown files in ClarifAI, showing how the concept promotion pipeline automatically generates Tier 3 concept documents.

## Overview

The ClarifAI concept creation system follows this pipeline:

1. **Text Processing** → Extract noun phrases from claims and summaries
2. **Concept Detection** → Identify similar concepts or promote new ones
3. **Neo4j Integration** → Create (:Concept) nodes for promoted concepts
4. **Tier 3 File Creation** → Generate `[[Concept]]` Markdown files in the vault

## The Complete Workflow

### Step 1: Noun Phrase Extraction

When processing claims or summaries, ClarifAI extracts noun phrases that could become concepts:

```python
from clarifai_shared.noun_phrase_extraction import NounPhraseExtractor

# Initialize extractor
extractor = NounPhraseExtractor()

# Process a claim or summary
result = extractor.extract_from_text(
    text="Machine learning is revolutionizing data analysis in healthcare.",
    source_node_id="claim_123",
    source_node_type="claim",
    clarifai_id="doc_456"
)

# This extracts candidates like:
# - "machine learning"
# - "data analysis" 
# - "healthcare"
```

### Step 2: Concept Detection and Promotion

The system then analyzes each candidate to determine if it should be merged with existing concepts or promoted to a new concept:

```python
from clarifai_shared.concept_detection import ConceptDetector

detector = ConceptDetector()

# Process a batch of candidates
detection_batch = detector.process_candidates_batch(candidates)

# Results contain actions:
# - MERGED: Similar concept already exists
# - PROMOTED: New concept should be created
```

### Step 3: Concept Node Creation

Promoted concepts become (:Concept) nodes in the Neo4j graph:

```python
from clarifai_shared.graph import Neo4jGraphManager

neo4j_manager = Neo4jGraphManager()

# Create concept nodes for promoted candidates
concepts = neo4j_manager.create_concepts(promoted_concept_inputs)

# Each concept gets:
# - Unique concept_id (e.g., "concept_machine_learning_123")
# - Source traceability to original claim/summary
# - Timestamp and version tracking
```

### Step 4: Tier 3 File Generation

Finally, each new concept automatically gets a Tier 3 Markdown file:

```python
from clarifai_shared.tier3_concept import ConceptFileWriter

writer = ConceptFileWriter()

# Creates a file for each concept
for concept in created_concepts:
    success = writer.write_concept_file(concept)
```

## Generated File Structure

### Filename Generation

Concept filenames are generated from the concept text using filesystem-safe transformations:

- **Input**: "machine learning"
- **Filename**: `machine_learning.md`
- **Rules**:
  - Convert to lowercase
  - Replace spaces with underscores
  - Remove special characters
  - Ensure uniqueness

### File Content Template

Each generated concept file follows this structure:

```markdown
## Concept: machine learning

This concept was automatically extracted and promoted from processed content.

### Examples
<!-- Examples will be added when claims are linked to this concept -->

### See Also
<!-- Related concepts will be added through concept linking -->

<!-- clarifai:id=concept_machine_learning_123 ver=1 -->
^concept_machine_learning_123
```

## Key Components Explained

### ClarifAI ID and Anchors

Each concept file includes two important markers:

1. **ClarifAI ID Comment**: `<!-- clarifai:id=concept_machine_learning_123 ver=1 -->`
   - Links the file to the Neo4j (:Concept) node
   - Includes version number for tracking changes
   - Used for synchronization between vault and graph

2. **Obsidian Anchor**: `^concept_machine_learning_123`
   - Allows direct linking to this concept from other notes
   - Enables Obsidian's block reference system
   - Supports concept relationship mapping

### File Location

Concept files are created in the configured concepts directory:

```yaml
# In settings/clarifai.config.yaml
paths:
  concepts: "concepts"  # Creates files in vault/concepts/
```

## Integration with Obsidian

The generated concept files integrate seamlessly with Obsidian:

### Linking to Concepts

Reference concepts in your notes using standard Obsidian syntax:

```markdown
The advances in [[machine learning]] have transformed how we approach data analysis.

You can also link to specific concept anchors:
![[machine_learning#^concept_machine_learning_123]]
```

### Concept Graph Visualization

Obsidian's graph view will show relationships between:
- Source documents (Tier 1 files)
- Generated concepts (Tier 3 files)
- Claims and summaries that reference concepts

## Automated Workflow Example

Here's how the complete pipeline works in practice:

```python
from clarifai_core.concept_processor import ConceptProcessor

# Initialize the processor (handles all steps automatically)
processor = ConceptProcessor()

# Process a block (claim or summary)
result = processor.process_block_for_concepts(
    block={
        "clarifai_id": "claim_456",
        "semantic_text": "Machine learning algorithms are improving medical diagnosis accuracy."
    },
    block_type="claim"
)

# Result includes:
# - Extracted noun phrases: ["machine learning algorithms", "medical diagnosis"]
# - Detection actions: ["promoted", "merged"]
# - Created concept files: ["machine_learning_algorithms.md"]
# - Neo4j concept nodes created
```

## Configuration

Customize concept creation behavior in your `settings/clarifai.config.yaml`:

```yaml
concept_detection:
  similarity_threshold: 0.85  # Higher = more strict concept merging
  
embedding:
  default_model: "sentence-transformers/all-MiniLM-L6-v2"
  
paths:
  concepts: "concepts"  # Where concept files are created
```

## Error Handling

The system includes robust error handling:

- **File Write Failures**: Logged but don't stop concept node creation
- **Database Errors**: Concept promotion continues without file creation
- **Network Issues**: Embedding failures fallback gracefully
- **Duplicate Prevention**: Existing files are never overwritten

## Monitoring and Logging

Track concept creation through structured logs:

```bash
# View concept creation activity
grep "Created.*Tier 3 Markdown files" clarifai.log

# Monitor concept promotion rates
grep "promoted concepts" clarifai.log
```

## Next Steps

- **Concept Linking**: Connect related concepts through manual editing
- **Example Addition**: Add real-world examples to concept files
- **Relationship Mapping**: Use Obsidian's graph view to explore concept networks
- **Custom Templates**: Modify concept file templates in the codebase

The concept creation system provides a foundation for building a comprehensive knowledge graph that grows automatically as you process more content through ClarifAI.
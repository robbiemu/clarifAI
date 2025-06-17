# Tutorial: Using the Noun Phrase Extractor

This tutorial provides a step-by-step guide to using the `NounPhraseExtractor` to process nodes from your knowledge graph.

## Prerequisites

- A running Neo4j instance with some `(:Claim)` or `(:Summary)` nodes.
- A configured PostgreSQL database with the `pgvector` extension.
- Your `.env` file should be configured with database credentials.

## Step 1: Initialize the Extractor

The `NounPhraseExtractor` is designed to be self-contained. It initializes its own database connections and models based on the central configuration.

```python
from clarifai_shared.noun_phrase_extraction import NounPhraseExtractor
from clarifai_shared.config import load_config

# Ensure your configuration is loaded
# This will pick up settings from your .env and clarifai.config.yaml
config = load_config()

# Initialize the extractor
# This will automatically connect to databases and load the spaCy model.
try:
    extractor = NounPhraseExtractor(config)
    print("✅ Noun Phrase Extractor initialized successfully.")
except Exception as e:
    print(f"❌ Failed to initialize extractor: {e}")
    # Ensure you have run 'python -m spacy download en_core_web_sm'
```

## Step 2: Run the Extraction Process

The primary method is `extract_from_all_nodes()`, which fetches all `(:Claim)` and `(:Summary)` nodes and processes them.

```python
# Run the full extraction and storage pipeline
extraction_result = extractor.extract_from_all_nodes()

if extraction_result.is_successful:
    print("\n📊 Extraction Summary:")
    print(f"  - Nodes Processed: {extraction_result.total_nodes_processed}")
    print(f"  - Phrases Extracted: {extraction_result.total_phrases_extracted}")
    print(f"  - Processing Time: {extraction_result.processing_time:.2f} seconds")
else:
    print(f"\n❌ Extraction failed: {extraction_result.error}")

# You can also inspect the extracted candidates before storage
# (Note: the main method stores them automatically)
print("\n🔍 Sample of Extracted Candidates:")
for candidate in extraction_result.candidates[:5]:
    print(f"  - Original: '{candidate.text}' -> Normalized: '{candidate.normalized_text}' (from {candidate.source_node_type} {candidate.source_node_id})")
```

## Step 3: Verify the Results

After running the extractor, you can verify the results in your PostgreSQL database.

Connect to your `clarifai` database and run:
```sql
SELECT
    metadata_->>'normalized_text' as phrase,
    metadata_->>'status' as status,
    metadata_->>'source_node_type' as source_type
FROM
    concept_candidates
ORDER BY
    id DESC
LIMIT 10;
```

You should see the newly extracted and normalized noun phrases with a status of `"pending"`. These candidates are now ready for the next step in the pipeline: concept detection and promotion.

## Step 4: Working with Individual Nodes

For more targeted processing, you can also extract from specific node types:

```python
# Extract only from Claim nodes
claim_result = extractor.extract_from_node_type("Claim")

# Extract only from Summary nodes  
summary_result = extractor.extract_from_node_type("Summary")

print(f"Claims: {claim_result.total_phrases_extracted} phrases")
print(f"Summaries: {summary_result.total_phrases_extracted} phrases")
```

## Step 5: Advanced Usage - Custom Filtering

You can also process nodes with custom filters:

```python
# Extract from nodes with specific properties
custom_result = extractor.extract_with_filter(
    node_types=["Claim", "Summary"],
    where_clause="n.confidence > 0.8",  # Only high-confidence nodes
    limit=100  # Process only first 100 matching nodes
)
```

## Common Examples

### Example 1: Processing a Specific Document

```python
# Find and process all claims from a specific document
document_id = "doc_123"
result = extractor.extract_with_filter(
    node_types=["Claim"],
    where_clause=f"n.document_id = '{document_id}'"
)

print(f"Extracted {result.total_phrases_extracted} phrases from document {document_id}")
```

### Example 2: Monitoring Progress

```python
import time

print("Starting noun phrase extraction...")
start_time = time.time()

# Process in smaller batches to monitor progress
batch_size = 50
total_processed = 0

while True:
    result = extractor.extract_with_filter(
        node_types=["Claim", "Summary"],
        where_clause="NOT EXISTS { (n)-[:HAS_CANDIDATE]->() }",  # Unprocessed nodes
        limit=batch_size
    )
    
    if result.total_nodes_processed == 0:
        break
        
    total_processed += result.total_nodes_processed
    elapsed = time.time() - start_time
    
    print(f"Processed {total_processed} nodes, {result.total_phrases_extracted} phrases in {elapsed:.1f}s")

print(f"✅ Extraction complete! Total nodes: {total_processed}")
```

### Example 3: Quality Control

```python
# Extract and validate results
result = extractor.extract_from_all_nodes()

# Check for common issues
if result.is_successful:
    candidates = result.candidates
    
    # Analyze phrase length distribution
    lengths = [len(c.normalized_text) for c in candidates]
    avg_length = sum(lengths) / len(lengths)
    
    print(f"📈 Quality Metrics:")
    print(f"  - Average phrase length: {avg_length:.1f} characters")
    print(f"  - Shortest phrase: {min(lengths)} characters")
    print(f"  - Longest phrase: {max(lengths)} characters")
    
    # Sample of normalized phrases
    print(f"\n📝 Sample Normalized Phrases:")
    for candidate in candidates[:10]:
        print(f"  - {candidate.normalized_text}")
```

## Troubleshooting

### Common Issues

1. **spaCy Model Not Found**
   ```bash
   python -m spacy download en_core_web_sm
   ```

2. **Database Connection Errors**
   - Verify your `.env` file has correct database credentials
   - Ensure PostgreSQL is running and accessible
   - Check that the `pgvector` extension is installed

3. **Memory Issues with Large Datasets**
   - Process in smaller batches using the `extract_with_filter()` method
   - Consider using the smaller spaCy model (`en_core_web_sm`)
   - Monitor system memory usage during extraction

4. **No Phrases Extracted**
   - Verify that your Neo4j database contains `(:Claim)` or `(:Summary)` nodes
   - Check that the nodes have text content in expected properties
   - Review the normalization settings in your configuration

### Performance Tips

- **Use Batch Processing**: The system automatically batches database operations for efficiency
- **Monitor Resource Usage**: Large extractions can be memory-intensive
- **Regular Maintenance**: Clean up old pending candidates periodically
- **Index Optimization**: Ensure your Neo4j database has appropriate indexes on node labels
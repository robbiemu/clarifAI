# Claimify Pipeline Integration Tutorial

This tutorial provides a complete walkthrough of integrating the Claimify pipeline with Neo4j graph storage, from initial setup to advanced usage patterns.

## Learning Objectives

By the end of this tutorial, you will be able to:
- Set up the complete Claimify pipeline with Neo4j integration
- Process text content and persist results to the knowledge graph
- Monitor and troubleshoot the integration
- Implement advanced integration patterns

## Prerequisites

- aclarai development environment set up
- Neo4j database running (local or remote)
- LLM access configured (OpenAI, Azure OpenAI, or local models)
- Basic understanding of Neo4j and graph databases

## Part 1: Environment Setup

### 1.1 Configuration Setup

Create or update your `settings/aclarai.config.yaml`:

```yaml
# Database configuration
database:
  host: "localhost"
  port: 7687
  user: "neo4j"
  password: "your_password"
  name: "aclarai"

# Claimify pipeline configuration
claimify:
  context_window:
    p: 3  # Previous sentences
    f: 1  # Following sentences
  models:
    selection: null
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

### 1.2 Verify Neo4j Connection

```python
from aclarai_shared.claimify.integration import create_graph_manager_from_config
from aclarai_shared.config import load_config

# Load configuration
config = load_config()

# Test Neo4j connection
try:
    graph_manager = create_graph_manager_from_config(config)
    print("✅ Neo4j connection successful")
    
    # Apply schema
    graph_manager.setup_schema()
    print("✅ Schema setup complete")
    
except Exception as e:
    print(f"❌ Neo4j connection failed: {e}")
    exit(1)
```

### 1.3 Test LLM Configuration

```python
from aclarai_shared.claimify import ClaimifyPipeline, load_claimify_config_from_file

# Load Claimify configuration
claimify_config = load_claimify_config_from_file("settings/aclarai.config.yaml")

# Test pipeline creation
try:
    pipeline = ClaimifyPipeline(config=claimify_config)
    print("✅ Claimify pipeline initialized")
except Exception as e:
    print(f"❌ Pipeline initialization failed: {e}")
    exit(1)
```

## Part 2: Basic Integration

### 2.1 Complete Integration Setup

```python
from aclarai_shared.claimify import (
    ClaimifyPipeline,
    SentenceChunk,
    ClaimifyContext,
    load_claimify_config_from_file
)
from aclarai_shared.claimify.integration import (
    ClaimifyGraphIntegration,
    create_graph_manager_from_config
)
from aclarai_shared.config import load_config

# Load configurations
main_config = load_config()
claimify_config = load_claimify_config_from_file("settings/aclarai.config.yaml")

# Initialize components
pipeline = ClaimifyPipeline(config=claimify_config)
graph_manager = create_graph_manager_from_config(main_config)
integration = ClaimifyGraphIntegration(graph_manager)

print("✅ Integration setup complete")
```

### 2.2 Process Sample Content

```python
# Sample sentences for processing
sample_sentences = [
    "The API endpoint received a malformed request.",
    "It caused a 400 Bad Request error to be returned.",
    "The error message indicated missing required parameters.",
    "This resulted in the client application failing to authenticate.",
    "The system logged the error for debugging purposes."
]

# Convert to sentence chunks
sentence_chunks = []
for i, text in enumerate(sample_sentences):
    chunk = SentenceChunk(
        text=text,
        source_id="tutorial_doc_001",
        chunk_id=f"chunk_{i:03d}",
        sentence_index=i
    )
    sentence_chunks.append(chunk)

print(f"Created {len(sentence_chunks)} sentence chunks")
```

### 2.3 Pipeline Processing

```python
# Process sentences through pipeline
results = []
for i, chunk in enumerate(sentence_chunks):
    # Build context window
    context = ClaimifyContext(
        current_sentence=chunk,
        preceding_sentences=sentence_chunks[max(0, i-claimify_config.context_window_p):i],
        following_sentences=sentence_chunks[i+1:i+1+claimify_config.context_window_f]
    )
    
    # Process through pipeline
    try:
        result = pipeline.process(context)
        results.append(result)
        
        # Log processing result
        status = "✅ Processed" if result.was_processed else "⏭️ Skipped"
        print(f"{status}: {chunk.text[:50]}...")
        
        if result.was_processed:
            print(f"  → Claims: {len(result.final_claims)}")
            print(f"  → Sentences: {len(result.final_sentences)}")
            
    except Exception as e:
        print(f"❌ Error processing: {chunk.text[:50]}... ({e})")
        
print(f"\nProcessing complete: {len(results)} results")
```

### 2.4 Persist to Neo4j

```python
# Persist results to Neo4j
try:
    claims_created, sentences_created, errors = integration.persist_claimify_results(results)
    
    print(f"\n📊 Persistence Results:")
    print(f"  Claims created: {claims_created}")
    print(f"  Sentences created: {sentences_created}")
    
    if errors:
        print(f"  Errors: {len(errors)}")
        for error in errors:
            print(f"    - {error}")
    else:
        print("  ✅ No errors")
        
except Exception as e:
    print(f"❌ Persistence failed: {e}")
```

## Part 3: Advanced Integration Patterns

### 3.1 Batch Processing with Error Handling

```python
def process_documents_batch(documents, batch_size=10):
    """Process multiple documents in batches with comprehensive error handling."""
    
    all_results = []
    total_claims = 0
    total_sentences = 0
    
    for doc_idx, document in enumerate(documents):
        print(f"\n📄 Processing document {doc_idx + 1}/{len(documents)}")
        
        # Convert document to sentence chunks
        chunks = []
        for i, sentence in enumerate(document['sentences']):
            chunk = SentenceChunk(
                text=sentence,
                source_id=document['id'],
                chunk_id=f"{document['id']}_chunk_{i:03d}",
                sentence_index=i
            )
            chunks.append(chunk)
        
        # Process chunks in batches
        doc_results = []
        for batch_start in range(0, len(chunks), batch_size):
            batch_chunks = chunks[batch_start:batch_start + batch_size]
            batch_results = []
            
            print(f"  Processing batch {batch_start//batch_size + 1} ({len(batch_chunks)} sentences)")
            
            for i, chunk in enumerate(batch_chunks):
                chunk_idx = batch_start + i
                context = ClaimifyContext(
                    current_sentence=chunk,
                    preceding_sentences=chunks[max(0, chunk_idx-claimify_config.context_window_p):chunk_idx],
                    following_sentences=chunks[chunk_idx+1:chunk_idx+1+claimify_config.context_window_f]
                )
                
                try:
                    result = pipeline.process(context)
                    batch_results.append(result)
                except Exception as e:
                    print(f"    ❌ Error processing chunk {chunk.chunk_id}: {e}")
                    continue
            
            # Persist batch to Neo4j
            if batch_results:
                try:
                    claims, sentences, errors = integration.persist_claimify_results(batch_results)
                    total_claims += claims
                    total_sentences += sentences
                    
                    print(f"    ✅ Batch persisted: {claims} claims, {sentences} sentences")
                    
                    if errors:
                        print(f"    ⚠️ Batch errors: {len(errors)}")
                        
                except Exception as e:
                    print(f"    ❌ Batch persistence failed: {e}")
            
            doc_results.extend(batch_results)
        
        all_results.extend(doc_results)
    
    return all_results, total_claims, total_sentences

# Example usage
sample_documents = [
    {
        'id': 'doc_001',
        'sentences': [
            "The authentication service experienced downtime.",
            "Users were unable to log into the application.",
            "The issue was caused by a database connection timeout.",
            "Service was restored after 30 minutes."
        ]
    },
    {
        'id': 'doc_002', 
        'sentences': [
            "The new feature deployment completed successfully.",
            "Performance metrics showed 15% improvement.",
            "User engagement increased by 8%.",
            "No critical issues were reported."
        ]
    }
]

results, total_claims, total_sentences = process_documents_batch(sample_documents)
print(f"\n🎯 Final Results: {total_claims} claims, {total_sentences} sentences")
```

### 3.2 Quality Monitoring and Analytics

```python
def analyze_processing_quality(results):
    """Analyze the quality and characteristics of processing results."""
    
    # Basic statistics
    total_sentences = len(results)
    processed_sentences = sum(1 for r in results if r.was_processed)
    total_claims = sum(len(r.final_claims) for r in results)
    total_sentence_nodes = sum(len(r.final_sentences) for r in results)
    
    # Processing rates
    selection_rate = processed_sentences / total_sentences if total_sentences > 0 else 0
    claims_per_processed = total_claims / processed_sentences if processed_sentences > 0 else 0
    
    # Quality metrics
    high_confidence_claims = 0
    low_confidence_claims = 0
    
    for result in results:
        for claim in result.final_claims:
            if hasattr(claim, 'confidence') and claim.confidence:
                if claim.confidence >= 0.8:
                    high_confidence_claims += 1
                elif claim.confidence <= 0.6:
                    low_confidence_claims += 1
    
    # Timing analysis
    processing_times = [r.total_processing_time for r in results if r.total_processing_time]
    avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
    
    # Error analysis
    error_count = sum(len(r.errors) for r in results)
    
    print(f"\n📈 Processing Quality Analysis:")
    print(f"  📊 Basic Metrics:")
    print(f"    Total sentences: {total_sentences}")
    print(f"    Processed: {processed_sentences} ({selection_rate:.1%})")
    print(f"    Claims extracted: {total_claims}")
    print(f"    Sentence nodes: {total_sentence_nodes}")
    print(f"    Claims per processed sentence: {claims_per_processed:.2f}")
    
    print(f"\n  🎯 Quality Metrics:")
    print(f"    High confidence claims: {high_confidence_claims}")
    print(f"    Low confidence claims: {low_confidence_claims}")
    print(f"    Processing errors: {error_count}")
    
    print(f"\n  ⏱️ Performance Metrics:")
    print(f"    Average processing time: {avg_processing_time:.3f}s")
    print(f"    Sentences per second: {1/avg_processing_time:.2f}" if avg_processing_time > 0 else "    Sentences per second: N/A")
    
    return {
        'selection_rate': selection_rate,
        'claims_per_processed': claims_per_processed,
        'high_confidence_claims': high_confidence_claims,
        'low_confidence_claims': low_confidence_claims,
        'avg_processing_time': avg_processing_time,
        'error_count': error_count
    }

# Analyze our results
quality_metrics = analyze_processing_quality(results)
```

### 3.3 Neo4j Query Examples

```python
def query_created_content(graph_manager, document_id=None):
    """Query the Neo4j database for created claims and sentences."""
    
    # Query claims
    if document_id:
        claims_query = """
        MATCH (c:Claim)-[:ORIGINATES_FROM]->(b:Block)
        WHERE b.id CONTAINS $doc_id
        RETURN c.id, c.text, c.entailed_score, c.coverage_score, c.decontextualization_score
        ORDER BY c.timestamp DESC
        """
        claims_params = {"doc_id": document_id}
    else:
        claims_query = """
        MATCH (c:Claim)
        RETURN c.id, c.text, c.entailed_score, c.coverage_score, c.decontextualization_score
        ORDER BY c.timestamp DESC
        LIMIT 10
        """
        claims_params = {}
    
    # Query sentences
    if document_id:
        sentences_query = """
        MATCH (s:Sentence)-[:ORIGINATES_FROM]->(b:Block)
        WHERE b.id CONTAINS $doc_id
        RETURN s.id, s.text, s.ambiguous, s.verifiable
        ORDER BY s.timestamp DESC
        """
        sentences_params = {"doc_id": document_id}
    else:
        sentences_query = """
        MATCH (s:Sentence)
        RETURN s.id, s.text, s.ambiguous, s.verifiable
        ORDER BY s.timestamp DESC
        LIMIT 10
        """
        sentences_params = {}
    
    try:
        with graph_manager.driver.session() as session:
            # Get claims
            claims_result = session.run(claims_query, claims_params)
            claims = list(claims_result)
            
            # Get sentences
            sentences_result = session.run(sentences_query, sentences_params)
            sentences = list(sentences_result)
            
            print(f"\n🔍 Database Query Results:")
            print(f"  📋 Claims found: {len(claims)}")
            for claim in claims[:5]:  # Show first 5
                print(f"    - {claim['c.text'][:60]}...")
                if claim['c.entailed_score']:
                    print(f"      Scores: E={claim['c.entailed_score']:.2f}, C={claim['c.coverage_score']:.2f}, D={claim['c.decontextualization_score']:.2f}")
            
            print(f"\n  📝 Sentences found: {len(sentences)}")
            for sentence in sentences[:5]:  # Show first 5
                print(f"    - {sentence['s.text'][:60]}...")
                print(f"      Properties: ambiguous={sentence['s.ambiguous']}, verifiable={sentence['s.verifiable']}")
            
            return claims, sentences
            
    except Exception as e:
        print(f"❌ Query failed: {e}")
        return [], []

# Query the database for our results
claims, sentences = query_created_content(graph_manager, "tutorial_doc_001")
```

## Part 4: Production Considerations

### 4.1 Error Recovery and Resilience

```python
import time
import logging
from typing import List, Optional

class ResilientClaimifyIntegration:
    """Production-ready Claimify integration with error recovery."""
    
    def __init__(self, pipeline, integration, max_retries=3, retry_delay=1.0):
        self.pipeline = pipeline
        self.integration = integration
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.logger = logging.getLogger(__name__)
    
    def process_with_retry(self, context, chunk_id: str) -> Optional[ClaimifyResult]:
        """Process a single context with retry logic."""
        
        for attempt in range(self.max_retries):
            try:
                result = self.pipeline.process(context)
                return result
                
            except Exception as e:
                self.logger.warning(
                    f"Processing attempt {attempt + 1} failed for {chunk_id}: {e}"
                )
                
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (2 ** attempt))  # Exponential backoff
                else:
                    self.logger.error(f"All attempts failed for {chunk_id}")
                    return None
    
    def persist_with_retry(self, results: List[ClaimifyResult]) -> tuple:
        """Persist results with retry logic."""
        
        for attempt in range(self.max_retries):
            try:
                return self.integration.persist_claimify_results(results)
                
            except Exception as e:
                self.logger.warning(
                    f"Persistence attempt {attempt + 1} failed: {e}"
                )
                
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (2 ** attempt))
                else:
                    self.logger.error("All persistence attempts failed")
                    return 0, 0, [f"Persistence failed after {self.max_retries} attempts: {e}"]

# Usage example
resilient_integration = ResilientClaimifyIntegration(pipeline, integration)
```

### 4.2 Performance Monitoring

```python
import time
import psutil
from dataclasses import dataclass
from typing import Dict, Any

@dataclass 
class PerformanceMetrics:
    """Performance monitoring for Claimify integration."""
    
    start_time: float
    sentences_processed: int = 0
    claims_created: int = 0
    sentences_created: int = 0
    errors: int = 0
    
    def duration(self) -> float:
        return time.time() - self.start_time
    
    def sentences_per_second(self) -> float:
        duration = self.duration()
        return self.sentences_processed / duration if duration > 0 else 0
    
    def success_rate(self) -> float:
        total = self.sentences_processed + self.errors
        return self.sentences_processed / total if total > 0 else 0
    
    def memory_usage_mb(self) -> float:
        return psutil.Process().memory_info().rss / 1024 / 1024
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'duration': self.duration(),
            'sentences_processed': self.sentences_processed,
            'claims_created': self.claims_created,
            'sentences_created': self.sentences_created,
            'errors': self.errors,
            'sentences_per_second': self.sentences_per_second(),
            'success_rate': self.success_rate(),
            'memory_usage_mb': self.memory_usage_mb()
        }

def monitor_integration_performance(documents):
    """Process documents with comprehensive performance monitoring."""
    
    metrics = PerformanceMetrics(start_time=time.time())
    
    print(f"🚀 Starting performance monitoring for {len(documents)} documents")
    
    for doc_idx, document in enumerate(documents):
        doc_start = time.time()
        
        # Process document...
        # (Implementation similar to previous examples)
        
        doc_duration = time.time() - doc_start
        print(f"  Document {doc_idx + 1} completed in {doc_duration:.2f}s")
        
        # Update metrics
        current_metrics = metrics.to_dict()
        print(f"  📊 Current rate: {current_metrics['sentences_per_second']:.2f} sentences/sec")
        print(f"  💾 Memory usage: {current_metrics['memory_usage_mb']:.1f} MB")
    
    # Final report
    final_metrics = metrics.to_dict()
    print(f"\n🏁 Final Performance Report:")
    for key, value in final_metrics.items():
        print(f"  {key}: {value}")
    
    return metrics
```

## Conclusion

This tutorial has covered:

1. **Environment Setup**: Configuration and connection verification
2. **Basic Integration**: Pipeline processing and Neo4j persistence
3. **Advanced Patterns**: Batch processing, error handling, and quality monitoring
4. **Production Considerations**: Resilience, performance monitoring, and optimization

### Next Steps

- **Evaluation Integration**: Set up evaluation agents to score claims (see evaluation system documentation)
- **Monitoring & Alerting**: Implement production monitoring for the integration pipeline
- **Scale Testing**: Test the integration with larger document sets
- **Custom Models**: Experiment with different LLM models for each stage

### Additional Resources

- **Architecture**: `docs/arch/on-claim_generation.md` - Detailed pipeline design
- **Neo4j Patterns**: `docs/arch/on-neo4j_interaction.md` - Graph database integration
- **Configuration**: `docs/guides/claimify_pipeline_guide.md` - Configuration reference
- **Troubleshooting**: Check logs and error patterns for common issues
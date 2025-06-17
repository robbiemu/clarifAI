# Noun Phrase Extraction Configuration Guide

This guide explains how to configure the Noun Phrase Extraction system in ClarifAI and manage embedding model changes effectively.

## Overview

The behavior of the noun phrase extractor is controlled through the `noun_phrase_extraction` section in your `settings/clarifai.config.yaml` file. This allows you to tune the spaCy model, normalization rules, and vector storage parameters.

## Configuration Parameters

Here is an example of the configuration block with explanations for each parameter:

```yaml
# In settings/clarifai.config.yaml

noun_phrase_extraction:
  # spaCy model to use for extraction. "en_core_web_trf" is more accurate
  # but larger and slower than the default "en_core_web_sm".
  spacy_model: "en_core_web_sm"
  
  # Normalization settings
  min_phrase_length: 2        # Minimum characters for a phrase after normalization.
  filter_digits_only: true   # If true, skips phrases that only contain digits.
  
  # Vector storage settings for concept_candidates
  concept_candidates:
    collection_name: "concept_candidates" # The name of the table in PostgreSQL.
    status_field: "status"      # The metadata field for tracking candidate status.
    default_status: "pending"   # The initial status for all new candidates.
```

### Tuning spaCy Model

-   **`en_core_web_sm` (Default):** Fast, small, and good for general-purpose extraction.
-   **`en_core_web_trf`:** Transformer-based model that offers higher accuracy, especially for complex or domain-specific text, at the cost of performance and resource usage. To use it, you must first install it: `python -m spacy download en_core_web_trf`.

### Normalization Rules

-   **`min_phrase_length`**: Prevents very short, often meaningless phrases (like single letters or acronyms) from cluttering the candidate pool.
-   **`filter_digits_only`**: Useful for excluding version numbers or identifiers that are extracted as noun phrases but are not true concepts.

## Embedding Model Management

### Single Source of Truth for Dimensions

The Noun Phrase Extraction system automatically determines the correct embedding dimension from your configured embedding model. This eliminates the need to manually synchronize dimension settings when changing models.

The system reads the embedding model configuration from:

```yaml
embedding:
  models:
    default: "sentence-transformers/all-MiniLM-L6-v2"  # 384 dimensions
```

When you change this model, the concept candidates storage automatically adapts to use the new dimension without additional configuration.

### Changing Embedding Models

**Important**: Changing an embedding model requires a complete data migration because existing vectors become incompatible.

#### The Migration Process

1. **Stop All ClarifAI Services**
   ```bash
   docker compose down
   ```

2. **Edit Configuration**
   Only change the model name in your `settings/clarifai.config.yaml`:
   ```yaml
   embedding:
     models:
       default: "sentence-transformers/all-mpnet-base-v2"  # 768 dimensions
   ```

3. **Clear Existing Vector Data**
   ```bash
   # Remove PostgreSQL data volume (destructive operation)
   docker volume rm clarifai_pg_data
   ```

4. **Restart Services**
   ```bash
   docker compose up -d
   ```
   The system will automatically:
   - Detect the new model's dimension (768)
   - Create new vector tables with the correct schema
   - Initialize empty concept_candidates storage

5. **Re-populate Data**
   Trigger a full vault re-processing to populate the new vector tables with embeddings from the new model.

### Why This Approach Works

This design provides several benefits:

- **User Simplicity**: Only one configuration change required
- **Automatic Adaptation**: The system self-configures to the new model's specifications
- **Error Prevention**: Eliminates dimension mismatch runtime errors
- **Clear Migration Path**: Forces explicit acknowledgment that model changes require data migration

### Supported Models

Any sentence-transformers model is supported. Popular options include:

- `sentence-transformers/all-MiniLM-L6-v2` (384 dim) - Fast, good quality
- `sentence-transformers/all-mpnet-base-v2` (768 dim) - High quality
- `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (384 dim) - Multilingual

The system will automatically download and configure any valid sentence-transformers model on first use.
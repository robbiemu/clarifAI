## 🧠 Purpose

This job ensures that each `(:Concept)` node and its corresponding entry in the vector index reflect the **current meaning** of its Tier 3 Markdown file in the Obsidian vault. It detects **semantic drift** caused by manual edits and updates the embedding and graph metadata accordingly.

---

## 📁 Motivation

Concept files in the vault may be edited by users or ClarifAI agents. These changes can alter the concept’s meaning, requiring a refreshed embedding to:

* Maintain accurate vector search results
* Detect similarity collisions
* Ensure claim-to-concept linking remains relevant

---

## 🧩 Input

* All files matching `vault/concepts/*.md`
* Each file contains:

  * Markdown text with semantic content
  * Embedded metadata block:
    `<!-- clarifai:id=concept_<slug> ver=3 -->`

---

## 🔧 Job Logic

### 1. **Iterate over each concept file**

```python
import os, hashlib
for file in os.listdir("vault/concepts"):
    if not file.endswith(".md"):
        continue

    concept_name = file[:-3]  # strip .md
    text = read_file(f"vault/concepts/{file}")
```

---

### 2. **Extract text for embedding and compute hash**

```python
def strip_metadata(md):
    return "\n".join([
        line for line in md.splitlines()
        if not line.startswith("<!-- clarifai:")
    ])

semantic_text = strip_metadata(text)
embedding_hash = hashlib.sha256(semantic_text.encode()).hexdigest()
```

---

### 3. **Compare to existing Neo4j hash**

```python
result = neo4j.run("""
    MATCH (c:Concept {name: $name}) RETURN c.embedding_hash
""", {"name": concept_name})

if result["embedding_hash"] == embedding_hash:
    continue  # No update needed
```

---

### 4. **Recompute embedding and update**

```python
embedding = embed_text(semantic_text)

vector_store.upsert(concept_name, embedding)

neo4j.run("""
    MATCH (c:Concept {name: $name})
    SET c.embedding_hash = $hash,
        c.last_updated = datetime()
""", {
    "name": concept_name,
    "hash": embedding_hash
})
```

---

## 🧾 Example

Suppose the user edits:

```markdown
# CUDA error

Common issue with PyTorch on Linux when using incompatible CUDA versions like 12.3 or 12.4. These may trigger “out of memory” or “invalid device function”.

<!-- clarifai:id=concept_cuda_error ver=4 -->
^concept_cuda_error
```

The next nightly job will:

1. Detect a new hash for this content
2. Recompute its embedding
3. Update both:

   * The `concepts` vector store (e.g., PGVector or hnswlib)
   * The `(:Concept)` node in Neo4j with `embedding_hash` and `last_updated`

---

## ✅ Outcome

* All `(:Concept)` nodes stay aligned with their Markdown definitions
* Vector search and similarity checks remain meaningful
* Changes are visible in the graph and vector layers with minimal latency

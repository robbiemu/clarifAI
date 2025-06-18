## 🧠 Purpose

This document defines how aclarai links extracted `(:Claim)` nodes to existing `(:Concept)` nodes using LLM-based classification. These links represent semantic relationships such as `SUPPORTS_CONCEPT`, `MENTIONS_CONCEPT`, and `CONTRADICTS_CONCEPT`. Each link carries metadata scores that capture the confidence, entailment, and informational coverage of the connection.

---

## 🧩 Inputs

For each claim:

* **Text of the `(:Claim)`**
* **Candidate `(:Concept)` nodes**, retrieved via vector similarity search from the `concepts` table (HNSW index, cosine similarity)
* **Optional context**:

  * Source sentence (if available)
  * Associated Tier 2 summary block

---

## 🛠️ Agent Design

### 🔧 Agent Name

`ClaimConceptLinkerAgent`

### 🔍 Inputs

```json
{
  "claim": "The user reported GPU crashes when using CUDA 12.3.",
  "concept": "CUDA error",
  "context": {
    "source_sentence": "The user's logs showed errors related to CUDA 12.3 after upgrading their drivers.",
    "summary_block": "- The user experienced issues when running Torch with CUDA 12.3 on Linux. ^blk_abc123"
  }
}
```

### 🧠 Prompt Structure

```text
You are a semantic classifier tasked with identifying the relationship between a claim and a concept.

Claim:
"The user reported GPU crashes when using CUDA 12.3."

Concept:
"CUDA error"

Context (optional):
- Source sentence: "The user's logs showed errors related to CUDA 12.3 after upgrading their drivers."
- Summary block: "- The user experienced issues when running Torch with CUDA 12.3 on Linux."

Instructions:
1. Classify the relationship:
   - SUPPORTS_CONCEPT: The claim directly supports or affirms the concept.
   - MENTIONS_CONCEPT: The claim is related to the concept but does not affirm or refute it.
   - CONTRADICTS_CONCEPT: The claim contradicts the concept.

2. Rate the strength of the relationship (0.0 to 1.0), where 1.0 is strong and direct.
3. Estimate whether the claim is entailed by its context (entailed_score).
4. Estimate how completely the claim covers the verifiable content of its context (coverage_score).

Output as JSON:
{
  "relation": "SUPPORTS_CONCEPT",
  "strength": 0.92,
  "entailed_score": 0.98,
  "coverage_score": 0.87
}
```

---

## 🧾 Output Schema

```json
{
  "relation": "MENTIONS_CONCEPT",
  "strength": 0.65,
  "entailed_score": 0.93,
  "coverage_score": 0.85
}
```

---

## 🧬 Graph Update

Create a relationship in Neo4j:

```cypher
MATCH (c:Claim {id: $claim_id}), (k:Concept {name: $concept_name})
MERGE (c)-[r:MENTIONS_CONCEPT]->(k)
SET r.strength = 0.65,
    r.entailed_score = 0.93,
    r.coverage_score = 0.85
```

Edge type (`MENTIONS_CONCEPT`) must match the `relation` output.

---

## 📁 Vault Update

* For each successful link, update the corresponding Tier 2 Markdown block to include the concept as a `[[wikilink]]`
* Use `aclarai:id` anchors to find and patch Markdown blocks in-place
* Perform atomic writeback using temp file + rename

---

## 🧪 Validation

* Spot check edge correctness by sampling claims and their links
* Confirm metadata ranges are reasonable (0.0 ≤ score ≤ 1.0)
* Confirm Markdown blocks link to the correct `[[Concept]]` pages

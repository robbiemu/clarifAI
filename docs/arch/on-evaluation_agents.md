# 🔍 Evaluation Roles

This document defines the evaluation agents in ClarifAI’s Claimify pipeline. These agents assess the quality of extracted claims — judging whether they are verifiable, complete, and independent. These evaluations help determine whether claims should be linked to concepts, retained in summaries, promoted into Tier 2 or 3 vault pages, or subjected to further evidence enrichment.

The evaluation agents are part of **Phase 2** of the pipeline, after claims have been extracted through ClarifAI’s implementation of Claimify’s four-stage process.

---

## 🧠 Evaluation Agents Overview

ClarifAI currently defines three evaluation agents:

| Role                  | Purpose                                                          | Output                             |
| --------------------- | ---------------------------------------------------------------- | ---------------------------------- |
| `entailment`          | Is the claim logically supported by its source?                  | `entailed_score: float`            |
| `coverage`            | Does the claim reflect all key verifiable content in the source? | `coverage_score: float`            |
| `decontextualization` | Can the claim be understood independently, without the source?   | `decontextualization_score: float` |

Each score is recorded in both the Markdown and graph layers of the system and is used in downstream logic such as filtering, promotion, linking, and evidence generation.

### Failure Handling:

* If this agent fails, it sets the score to `null`.
* Claims with any `null` score are **not written to Markdown**, **not linked to concepts**, and **not promoted**.
* They remain in the graph for diagnostic or future reprocessing purposes.

---

## ⚙️ Input Format

Each evaluation agent receives:

* A candidate claim (text, with `clarifai:id`)
* Its source block (Markdown block or structured sentence context)
* Linked concept metadata (if applicable)

Example:

```json
{
  "claim": "The EU approved €7.5 billion in climate funding in 2023.",
  "source": "In 2023, the EU finalized several funding agreements related to climate policy.",
  "clarifai_id": "blk_abc123",
  "concepts": ["climate policy", "EU funding"]
}
```

---

## 🧪 Agent: `entailment`

**Description:**
Evaluates whether the source logically supports the claim.

**Output:**

* `entailed_score: float` (0–1)

**Prompt structure:**

```
Premise: {source}
Hypothesis: {claim}
```

**Storage:**

* Graph edge (`:ORIGINATES_FROM`): `entailed_score`
* Markdown:

  ```markdown
  <!-- clarifai:entailed_score=0.91 -->
  ```

---

## 🧪 Agent: `coverage`

**Description:**
Measures how completely the claim captures the verifiable information in its source.

**Output:**

* `coverage_score: float`
* List of omitted verifiable elements

**Storage:**

* Graph edge: `coverage_score`
* Markdown:

  ```markdown
  <!-- clarifai:coverage_score=0.77 -->
  ```

**Missed Elements:**

* Each omitted verifiable unit becomes an `(:Element)` node
* Linked to the claim with `[:OMITS]`

```cypher
(:Claim)-[:OMITS]->(:Element {text: "European Commission"})
```

These nodes support claim expansion, subject generation, and RAG query enrichment.

---

## 🧪 Agent: `decontextualization`

**Description:**
Evaluates whether a generated claim is understandable and meaningful **without reference to its original sentence or question**. This ensures that the claim is suitable for re-use in summaries, concept pages, or downstream knowledge systems that require portable, context-independent statements.

---

**Output:**

* `decontextualization_score: float` (range: 0.0–1.0)
* If the agent fails (e.g., timeout, LLM error), this score is stored as `null`.

---

**Prompt:**

> “Can this claim be understood on its own, without access to the original sentence or question?”

---

**Storage:**

| Location          | Format                                                           |
| ----------------- | ---------------------------------------------------------------- |
| Graph edge        | `decontextualization_score` (float or null)                      |
| Markdown (Tier 1) | `<!-- clarifai:decontextualization_score=0.88 -->` (if included) |

Only claims that pass the quality threshold (see pipeline) are written to Markdown or used in summaries.

---

**Interpretation and Use:**

* This score is used **alongside entailment and coverage** to determine overall claim quality.
* These scores are **combined via geometric mean** to produce a single quality score.
* Claims with low geomean values or any `null` score are **excluded from promotion**, but retained in the graph.

---

## 🔧 Model Configuration

Each agent's LLM can be configured individually, or defaulted:

```yaml
model:
  claimify:
    default: "qwen-3-24b"
    entailment: "claude-3-opus"
    coverage: "gpt-4"
    decontextualization: "gpt-3.5"
```

---

## 🎚️ Thresholds

These scores affect filtering, linking, and promotion. Scores below threshold exclude the claim from downstream usage.

```yaml
threshold:
  claim_entailment: 0.85
  claim_coverage: 0.6
  claim_decontextualization: 0.7
```

---

## ❌ Failure Modes

If an agent fails after retries (e.g., timeout or model error), the resulting score is set to `null`.

Consumers must check for `null`. Claims with missing scores are:

* Excluded from concept linking
* Not promoted to summaries or concept pages

Example metadata:

```yaml
clarifai:entailed_score: null
```

---

### 🧩 Role in the Pipeline

The evaluation agents (`entailed`, `coverage`, `decontextualization`) produce scores that are used **after claim extraction**, during downstream processing. These scores guide:

* Concept linking
* Summary promotion
* Filtering and vault export
* Claim visibility and diagnostics

---

#### ✅ Scoring Interpretation

Instead of applying individual thresholds per score, ClarifAI uses a **geometric mean** of the three:

```python
geomean = (entailed_score * coverage_score * decontextualization_score) ** (1/3)
```

If any score is `null`, the geomean is not computed, and the claim is excluded.

---

#### 🔁 Promotion Logic

A claim is included in downstream workflows **only if**:

* All scores are present (non-null)
* Geomean ≥ system-wide quality threshold (e.g., 0.70)

Otherwise, it is retained in the graph, but:

* ❌ Not linked to concepts
* ❌ Not shown in Tier 2 or 3 vault files
* ❌ Not available to summaries or concept pages

---

#### 🛑 What This Prevents

* Concept pages anchored on vague or incomplete claims
* Summaries polluted with ambiguous or unverifiable content
* Claims with failed agents entering the markdown vault

---

#### ✅ Design Summary Table

| Score Field                 | Used For...                          | Inclusion Rule                      |
| --------------------------- | ------------------------------------ | ----------------------------------- |
| `entailed_score`            | Fidelity to source                   | Must be present and used in geomean |
| `coverage_score`            | Completeness of information          | Must be present and used in geomean |
| `decontextualization_score` | Portability and context-independence | Must be present and used in geomean |

note: the combined Geomean — indicating overall claim quality, which must exceed system threshold, is dynamic. It is not an actual field.
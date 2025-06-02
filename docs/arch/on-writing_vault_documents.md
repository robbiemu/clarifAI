# 🧠 On Writing Vault Documents

This document defines the expected output formats, content structure, and agent responsibilities for all agents that write Markdown documents to the ClarifAI vault. Each of these agents is scheduled and configured through the system and is responsible for maintaining consistent, structured, high-quality pages.

---

## 📘 Concept Summary Agent

**Output:** One `[[Concept]]` page per `(:Concept)` node.

**Purpose:** Define a single canonical concept using local evidence from the graph and vault.

**Input sources:**

* Supporting `(:Claim)` nodes (linked via `SUPPORTS_CONCEPT`, `MENTIONS_CONCEPT`, etc.)
* Referencing `(:Summary)` blocks
* Natural language examples from `(:Utterance)` nodes
* Related concepts from the `concepts` vector index

**Output structure:**

```markdown
## Concept: <concept name>

<definition paragraph>

### Examples
- <claim or utterance> ^clarifai:id
- ...

### See Also
- [[Related Concept A]]
- [[Related Concept B]]

<!-- clarifai:id=concept_<slug> ver=N -->
^concept_<slug>
```

**Notes:**

* No external search is used.
* If no claim is linked, the agent may skip generation (configurable).
* Tone is factual and concise.

---

## 📕 Subject Summary Agent

**Output:** One `[[Subject:XYZ]]` page per cluster of concepts.

**Purpose:** Summarize and contextualize a group of related concepts, based on semantic proximity or shared relationships.

**Input sources:**

* Grouped `(:Concept)` nodes (from HNSW-based clustering)
* Shared `(:Claim)` or `(:Summary)` references
* Optional: external web search or common knowledge augmentation

**Output structure:**

```markdown
## Subject: <name or synthesized theme>

<summary paragraph>

### Included Concepts
- [[Concept A]] — short internal blurb
- [[Concept B]] — short internal blurb

### Common Threads
- Summary of shared topics from claims
- Optional inline links to related subject pages

<!-- clarifai:id=subject_<slug> ver=N -->
^subject_<slug>
```

**Notes:**

* If a subject cluster lacks cohesion, the agent may frame it as an emerging or speculative theme, but always grounded in content from the vault.
* No invention: speculative/future framing only reflects existing claims or concept metadata.

---

## 📰 Trending Concepts Agent

**Output:**

* `Top Concepts.md`
* `Trending Topics - <date>.md`

**Purpose:** Provide a newsletter-style digest of the most central or recently active concepts.

**Input sources:**

* PageRank or degree score for `(:Concept)` nodes
* Frequency deltas from claim–concept links in recent time windows

**Output structure:**

```markdown
## Top Concepts

- [[Concept A]] — Short blurb explaining why it's central
- [[Concept B]] — Blurb from concept metadata or linked claims

---

## Trending This Week

- [[Concept X]] — Mentions up 250%; discussed in 4 summaries
- [[Concept Y]] — Frequently linked to new user content
```

**Notes:**

* Always uses bullet-point structure, with 1–2 sentence blurbs
* May reference summaries, claims, or relationship counts
* No multi-level bullets unless thematically required

---

## 📝 Tier 2 Summary Agent

**Output:** Markdown summaries embedded in Tier 2 conversation summary files.

**Purpose:** Aggregate and summarize selected Tier 1 blocks into semantically coherent groupings.

**Input sources:**

* Selected `(:Sentence)` and `(:Claim)` nodes
* Proximity in file and graph structure
* Utterance embeddings from pgvector

**Retrieval Notes:**

* The agent groups related blocks using `pg_vector_search`, a cosine similarity lookup over embeddings generated from Tier 1 content.
* The result is clustered blocks that form semantic neighborhoods for summarization.
* This selection process is non-agentic; the agent only writes the summaries based on the grouped results.

**Output structure:**

```markdown
- <summary sentence> ^clm_<id>
- ...

<!-- clarifai:id=clm_<id> ver=N -->
^clm_<id>
```

**Notes:**

* One agent run produces many Markdown blocks per summary file
* Summaries are self-contained and may contain linked concepts inline
* Follows same versioning and sync semantics as claims

# 📄 ClarifAI Graph–Vault Sync Design

### Overview

ClarifAI maintains a **bidirectional sync** between Obsidian Markdown files and a Neo4j knowledge graph. To do this reliably, each atomic unit of content—called a **block**—must be:

*   Uniquely identifiable
*   Versioned
*   Traceable to a graph node

This document defines what a “block” is, how it is marked in Markdown, and how the sync process detects changes, prevents overwrites, and updates Neo4j accordingly.

---

## 🧱 What is a Block?

A **block** is the smallest unit of content that is tracked individually in the graph.

| Vault Tier                     | Block Type                               | Example                                              |
| :----------------------------- | :--------------------------------------- | :--------------------------------------------------- |
| **Tier 1** (Raw Conversations) | A user utterance or sentence             | `"Alice: Let’s release v1.2 next week."`             |
| **Tier 2** (Summaries)         | A paragraph, bullet, or summary sentence | `• Alice proposed releasing v1.2 next week.`         |
| **Tier 3** (Concept Pages)     | A definition, claim, or evidence entry   | `• Release cadence is discussed in 3 conversations.` |
| **Tier 3/Global**              | A full, agent-generated report/summary   | `Top Concepts.md`, `Trending Topics - 2024-05-22.md` |

---

## 🌿 How Blocks Are Marked in Markdown

ClarifAI tracks content at different granularities, and each tracked unit (a "block" in ClarifAI's terminology) is marked with unique identifiers and versioning information using **invisible HTML comments**. These comments are placed either *inline* within a file for smaller content units, or *at the file level* for entire agent-generated documents.

### 1. Inline Block-Level Marking

For individual sentences, paragraphs, or claims within a Markdown file, markers are embedded directly after the content.

```markdown
Some text of the claim or summary. <!-- clarifai:id=clm_abc123 ver=2 -->
^clm_abc123
```

| Marker                                  | Purpose                                                                     |
| :-------------------------------------- | :-------------------------------------------------------------------------- |
| `<!-- clarifai:id=clm_abc123 ver=2 -->` | Hidden HTML comment for sync logic. Holds the unique ID and version number. |
| `^clm_abc123`                           | Obsidian block anchor. Enables links like `[[file#^clm_abc123]]`.           |

These markers travel with the text. If a user moves or reorders content, the ID and version stay intact.

### 2. File-Level Marking for Agent-Generated Pages

For pages that are generated entirely by ClarifAI agents (e.g., `Top Concepts.md`, `Trending Topics - {date}.md`, `[[Subject:XYZ]].md`), the `clarifai:id` and `ver=` markers apply to the **entire file content**. These markers are placed as an invisible HTML comment at the **very end of the file**.

```markdown
## Trending This Week

- [[Concept X]]
- [[Concept Y]]

<!-- clarifai:id=file_trending_20240522 ver=1 -->
```

*   The `clarifai:id` (e.g., `file_trending_20240522`, `subject_gpu_errors`) provides a unique ID for the entire file.
*   The `ver=` (e.g., `ver=1`) is the version number for the entire file content, which increments on any semantic change.
*   The ID format (e.g., `file_`, `subject_`, `concept_`) will indicate the type of generated page.

This consistent HTML comment approach ensures robust tracking while maintaining compatibility with Obsidian and other Markdown parsers. When ClarifAI processes these files, it hashes the *entire semantic content* (excluding these markers) to detect changes for versioning.

---

## 🔁 Sync Strategy

### 🔎 File Watcher

*   Runs in the background.
*   Watches for `.md` changes in Tier 2 and Tier 3 folders.
*   Batches events (e.g., using `watchdog` in Python or `chokidar` in JS).

### 🧠 Block Diffing

1.  Parse old and new versions of a file into a Markdown Abstract Syntax Tree (AST).
2.  Scan for `clarifai:id` comments.
3.  Build a mapping: `{id: (version, content)}`.

### ✏️ Change Types

| Change               | Action                                                          |
| :------------------- | :-------------------------------------------------------------- |
| **New block**        | Add new node in Neo4j: `CREATE (:Claim {id, ver=1, text, ...})` |
| **Edited block**     | If version matches graph: `SET ver = ver+1, text = $new`        |
| **Missing block**    | Optionally `DETACH DELETE` in Neo4j, or flag as `archived`      |
| **Version mismatch** | Skip update. Flag conflict. Log: “Vault out of sync with graph.”|

### 🧷 Atomic Writeback

When ClarifAI modifies a `.md` file:

1.  Generate updated Markdown with inserted/updated `clarifai:id` comments.
2.  Write to `.filename.md.tmp`.
3.  `fsync()`.
4.  `rename(tmp, filename.md)`.

This ensures that Obsidian or git sees either the old file or the fully updated file—never a partially written file.

---

## 🪪 Conflict Detection

Each block’s `ver=N` (within its HTML comment) lets the system detect concurrent edits:

*   Graph holds version `N`.
*   Vault sends update for version `N`.
*   Graph increments to `N+1`.
*   If graph already had `N+1`, the update is rejected—vault was stale.

Fallback: log it, surface a `<!-- clarifai:conflict ... -->` comment, or queue it for review.

---

## 🧠 Context Window for Claimify Processing

Claimify never judges a sentence in total isolation. Each **focal block** is processed with a *fixed, finite* slice of neighbouring sentences:

| Stage          | `p` (sentences before) | `f` (sentences after) |
| :------------- | :--------------------- | :-------------------- |
| Selection      | 5                      | 5                     |
| Disambiguation | 5                      | 0                     |
| Decomposition  | 5                      | 0                     |

> **WINDOW** = `max(p, f)` across all stages → **5** in the default configuration.

### One‑Pass Batch Algorithm

1.  **Dirty detection** – Hash each block’s visible text; any change marks that block *dirty*.
2.  **Window expansion (non‑transitive)** – For every dirty index *i*, add indices `i‑WINDOW … i+WINDOW` to a `set<int>`.
3.  **Deduplicate** – The set contains every block that *could* be in‑prompt for any dirty block.
4.  **Single Claimify pass** – Run Claimify once per block in the set, supplying the exact `p`, `f` required by each stage.
5.  **Graph update** – Increment `ver` on every block in the set (claims may change even if the text didn’t).

### Why this Terminates

*   The expansion is **one hop only**; neighbours are *not* further expanded.
*   The size of the batch is bounded by `11` sentences per dirty block with defaults (≤ file length overall).
*   No block is queued twice in the same cycle.

An edit to `S[i]` therefore triggers **exactly one batch**, covers all sentences Claimify can see (`±5`), and halts.

### Changing the Window

If you later adjust `p` or `f`, run a single full‑vault migration that reprocesses every block once with the new parameters. Routine edits then continue with the new window.

---

## 🏭 Nightly Reconciliation

A daily job should:

*   Walk the vault
*   Parse all known `clarifai:id` blocks (including file-level IDs)
*   Hash the visible text
*   Compare to graph values
*   Queue any drifted blocks for reprocessing

---

## ✅ Summary of Guarantees

*   Sync is **block-level**, not file-level (though files can be treated as single blocks).
*   Sync is **optimistic**—it never overwrites user edits without a version check.
*   Sync is **content-aware**—it diffs ASTs, not lines.
*   Sync is **safe**—file writes are atomic.
*   Claimify block processing always respects local context windows.

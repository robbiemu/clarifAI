# 🧭 ClarifAI UX Overview

This document describes the user-facing structure of ClarifAI, with updated assumptions from the finalized architecture and sprint planning through Sprint 5.

---

## **1. Importing Conversations**

* **Primary Interface:**
  File picker allows import of `.json` ChatGPT exports or other structured/unstructured formats.

* **Format Detection:**
  The system uses pluggable format handlers — no dropdowns required.

* **Live Transcript & Feedback:**
  Real-time status for import success, duplicates, or fallback usage.

* **Post-import Summary:**
  Indicates number of files imported, skipped, or rejected, with links to affected entries.

---

## **2. Reviewing & Managing Extracted Claims**

* **Primary Interface:**
  Extracted claims are inserted directly into Obsidian as Markdown blocks with versioned anchors.

* **Claim Metadata Display:**
  Each claim is annotated with its evaluation scores: `entailment`, `coverage`, and `decontextualization` (indicating how well the claim is supported, how complete its content is, and how independent it is from context).

* **Claim Identification:**
  Internal claim IDs are accessible for debugging or linking but remain hidden by default in Obsidian.

* **Claim Review UX:**
  ClarifAI supports manual edits to claim blocks; edits trigger reprocessing when drift is detected.

---

## **3. Concepts & Knowledge Graph (Tier 3)**

* **Concept Files:**
  Canonical concepts are written as Markdown pages (`[[Concept]]`) and can reside anywhere in the vault (default: co-mingled).

* **Concept Links:**
  Claims and summaries may auto-link to concepts via `[[wikilink]]`. These are also reflected in the Neo4j graph.

* **Concept Metadata:**
  ClarifAI tracks a content-derived `embedding_hash` on each concept node to detect drift. The actual embedding is stored in a vector DB.

* **Nightly Sync Jobs:**
  Embeddings are refreshed nightly. If vault edits alter the concept meaning, the system updates the vector DB and graph node accordingly.

---

## **4. Automation Control & Config**

* **Configuration Options:**
  ClarifAI supports configuration through either:

  * a YAML file (`clarifai.config.yaml`), or
  * a lightweight UI panel (future)

* **Configurable Parameters Include:**

  * Claimify window size (`p`, `f`)
  * Similarity thresholds for deduplication
  * Model backend selection per agent
  * Agent enable/disable toggles

* **Automation Control:**

  * "Pause automation" supported via:

    * File flag (`.clarifai_pause`) in vault root
    * UI toggle (future)
  * Scheduler supports override/disable per job via config

---

## **5. Future Panels**

Planned UI panels include:

* **Import Activity & Status Viewer**
* **Claim Audit and Comparison View**
* **Concept Merge Suggestions**
* **Automation Settings Page (runtime overrides)**

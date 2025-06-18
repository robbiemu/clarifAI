# aclarai: Technical Overview

This document outlines the technical architecture and workflow of **aclarai**, an AI-powered system designed to transform your digital conversations into a structured, interconnected knowledge base within Obsidian.

---

## I. Core Objectives

aclarai's primary goal is to leverage LlamaIndex agents to achieve the following:

* **Ingest and Standardize Conversations:** Take various conversation formats (like JSON exports) and convert them into a consistent Markdown format.
* **Manage Duplicates:** Effectively detect and handle duplicate conversations to maintain a clean knowledge base.
* **Extract Factual Claims:** Identify and extract factual statements from dialogues, rigorously evaluating them against [Claimify](https://arxiv.org/pdf/2502.10855)-inspired quality principles (entailment, coverage, and decontextualization).
* **Generate Multi-Tier Obsidian Documents:** Create a structured hierarchy of Markdown files within your Obsidian vault:
  * **Tier 1: Raw Conversation Histories:** The original, processed conversations, with precise internal links (Markdown block IDs) for easy reference.
  * **Tier 2: Conversation Summaries:** Concise summaries of each conversation, linking extracted claims back to Tier 1 and key concepts to Tier 3.
  * **Tier 3: Key Concept Pages:** Dedicated pages for important ideas and themes, linking back to relevant Tier 2 summaries and cross-linking with other concepts.
* **Integrate Vector Embeddings & Knowledge Graph:** Utilize both semantic search capabilities (via vector embeddings) and a structured knowledge graph (Neo4j, managed by LlamaIndex) to model and manage the relationships within your Obsidian vault. This graph includes rich semantic relationships and quality attributes for claims.
* **Maintain Graph-Vault Synchronization:** Ensure the internal knowledge graph accurately reflects the current state of your Obsidian files.

---

## II. Key Components & Technologies

aclarai's foundation relies on the following core elements:

* **Obsidian Vault:** This is the user's primary interface, serving as the storage location for all generated Markdown documents.
* **Robust Configuration System:** A file-based default configuration system that ensures consistency and user-customization. Uses a three-tier hierarchy (default template → user overrides → environment variables) with easy restoration capabilities.
* **Vector Store (LlamaIndex Managed):** Powers semantic search, similarity detection, and Retrieval-Augmented Generation (RAG). It efficiently handles long conversations by chunking them into smaller segments for embedding, ensuring that even lengthy dialogues can be processed and queried effectively without hitting LLM context limits.
* **Knowledge Graph (Neo4j via LlamaIndex):** This is the "brain" of aclarai, explicitly modeling relationships between different types of information (conversations, summaries, claims, sentences, and concepts).
    *   `Claim` nodes store quality evaluation scores for each extracted claim: `entailed_score`, `coverage_score`, and `decontextualization_score` (each ranging from 0.0 to 1.0).
    *   Relationships are defined with specific semantics (e.g., `ORIGINATES_FROM`, `SUPPORTS_CONCEPT`, `CONTRADICTS_CONCEPT`, `ENTAILS_CLAIM`) to create a precise and queryable graph.
    It provides a structured understanding of your vault's interconnectedness.
* **Large Language Models (LLMs):** These are the core intelligence, used for critical tasks such as:
  * Claim extraction and quality assessment (following Claimify principles).
  * Conversation summarization.
  * Concept identification.
  * Definition generation.
  * Relation classification (e.g., determining if a claim supports or contradicts a concept).

---

## III. Agents & Workflow

aclarai's operations are orchestrated through a series of intelligent agents across distinct phases:

### Phase A: Ingestion & Pre-processing

1.  **Input Staging & Format Conversion:**
    * **Purpose:** Prepares diverse input formats for processing.
    * **Process:** New conversation files (e.g., ChatGPT JSON, AI Studio logs) are placed in a staging directory. A **Format Conversion Manager** uses a **Plugin System** to convert these into a standardized Markdown for Tier 1, preserving semantic structure (speakers, timestamps).
    * **Output:** Standardized Markdown files in a "pre-processed" staging area.

2.  **Duplicate Detection & Vault Integration:**
    * **Purpose:** Prevents redundant data and integrates unique conversations into Obsidian.
    * **Process:**
      * Each pre-processed file is hashed and embedded.
      * **aclarai** checks for exact hash duplicates and uses vector similarity to detect near-duplicates against a **Manifest & Database** of already processed conversations.
      * Unique conversations are given a canonical filename, moved into the Tier 1 directory within your Obsidian vault, and their details (including embeddings) are added to the Vector Store and manifest.

### Phase B: Vault Synchronization & Knowledge Graph Update

This phase ensures the knowledge graph accurately reflects your Obsidian vault, ideal for running before new batches or after external vault changes.

3.  **Vault & Graph Synchronization:**
    * **Purpose:** Maintains consistency between the Knowledge Graph and your Obsidian vault.
    * **Process:** **aclarai** scans specified Obsidian directories (Tiers 1, 2, 3). It compares file checksums/timestamps with the graph's records. It creates new basic graph nodes for files found in Obsidian but not the graph, and flags or removes nodes for files deleted from Obsidian. This establishes the correct "canvas" for detailed processing.

### Phase C: Claim Extraction, Summarization, and Linking

4.  **Input Processing & Segmentation (Tier 1 Enhancement):**
    * **Purpose:** Prepares new Tier 1 conversations for in-depth analysis.
    * **Process:** Newly added Tier 1 files are segmented into sentences/utterances. Crucially, unique Markdown block identifiers (e.g., `^blockIdxyz`) are inserted at the end of each segment within the Tier 1 file itself, enabling precise linking. The Vector Store is updated to reflect these changes. These segments form `:Block` nodes in the Knowledge Graph.

5.  **Claimify-Powered Claim Extraction & Quality Assessment:**
    * **Purpose:** Extracts claims from conversations and assesses their quality based on Claimify principles.
    * **Process:** **aclarai** employs a Claimify-inspired methodology for each sentence/utterance identified in Step 4:
        * **5a. Claim Generation & Quality Scoring (Claimify Run):** For each sentence, a process inspired by Claimify generates 0-N simple candidate claims. Each candidate claim is then assessed against three quality principles, resulting in quality scores:
            * `entailed_score: Float` (Source sentence logically implies the claim, e.g., NLI score ≥ 0.9)
            * `coverage_score: Float` (Claim retains all crucial facts from the source sentence)
            * `decontextualization_score: Float` (Claim can be understood independently without additional context, resolving pronouns and including necessary qualifiers like time, location, and scope)
        * **5b. Quality-Based Filtering & Node Creation:**
            * **High-Quality Claims:** Claims that meet all evaluation thresholds (`entailed_score`, `coverage_score`, and `decontextualization_score`) are promoted to `(:Claim)` nodes in the Knowledge Graph and included in the user-facing knowledge base through Markdown files.
            * **Failed/Low-Quality Claims:** Claims that do not meet quality standards (e.g., an agent returns a null or sub-threshold score) are not output to any Markdown file or used for linking. They may be retained internally as graph entries tagged with null scores for debugging purposes, but they are effectively filtered out of the user-facing knowledge base.
            * **Ambiguous Statements:** For sentences where claim extraction fails entirely or yields highly ambiguous results, these may be preserved as `(:Sentence)` nodes in the graph (with flags like `ambiguous: true`) for potential future review, but they do not generate claims or contribute to the structured knowledge base.
    * **Output:** High-quality `Claim` nodes (with quality attributes) in the Knowledge Graph, all linked to their originating `Block` in Tier 1. Lower-quality or failed extractions are quarantined from the user-facing vault.

6.  **Conversation Summary & Tier 2 Generation:**
    * **Purpose:** Creates the concise Tier 2 summary documents.
    * **Process:** A new summary Markdown file (`:Summary` node in KG) is generated for each conversation, organizing only the high-quality extracted claims and reflecting the conversational flow. Markdown links are embedded from claims and sections in the summary directly back to the exact origin in the Tier 1 raw conversation using the block IDs. Each `(:Claim)` included in the summary is linked via a `(:Claim)-[:SUMMARIZED_IN]->(:Summary)` edge in the Knowledge Graph. This summary's content is then added to the Vector Store.

7.  **Key Concept Identification, Linking & Relation Enrichment:**
    * **Purpose:** Identifies recurring concepts, creates/updates Tier 3 pages, establishes comprehensive links with semantic richness, and performs relation enrichment.
    * **Process:**
      * An LLM-powered **Concept Extractor** identifies candidate concepts from Tier 2 summaries and high-quality claims.
      * A **Vault Knowledge Query Tool** (leveraging the Knowledge Graph and Vector Store) checks for existing concept pages (`:Concept` nodes) or similar ideas.
      * A **Concept Page & Graph Management Tool** then:
        * Creates new `[[Concept Name]].md` (Tier 3) pages for novel concepts (creating corresponding `:Concept` nodes). These include LLM-generated definitions and initial links back to the current Tier 2 summary.
        * Updates existing Tier 3 pages by appending links to new relevant Tier 2 summaries.
        * Transforms mentions of identified key concepts within the Tier 2 summary files into `[[wikilinks]]` pointing to their respective Tier 3 pages.
      * **Relation Classification & Graph Enrichment (Phase D equivalent):**
        * For `(Claim, Concept)` pairs, an LLM relation-classifier determines the nature of their relationship:
          * `(:Claim)-[:SUPPORTS_CONCEPT {strength: Float, entailed_score: Float, coverage_score: Float}]->(:Concept)`: Created if the claim provides positive evidence for the concept AND the claim meets quality criteria (high `entailed_score`, `coverage_score`, and `decontextualization_score`). The `strength` property captures the classifier's confidence; quality scores from the claim evaluation are stored for weighted evidence.
          * `(:Claim)-[:CONTRADICTS_CONCEPT {strength: Float, entailed_score: Float, coverage_score: Float}]->(:Concept)`: Created if the LLM detects semantic negation or refutation and the claim meets quality standards.
          * `(:Claim)-[:MENTIONS_CONCEPT]->(:Concept)`: Used as a fallback if a claim mentions a concept but doesn't meet the strict quality criteria for `SUPPORTS_CONCEPT` or `CONTRADICTS_CONCEPT` (e.g., lower decontextualization or coverage scores).
        * Other claim-to-claim relationships like `(:Claim)-[:ENTAILS_CLAIM]->(:Claim)` or `(:Claim)-[:REFINES_CLAIM]->(:Claim)` can be identified using NLI or other LLM tasks.
      * **(Advanced): Cross-Concept Linking:** Periodically, **aclarai** can analyze the Knowledge Graph for relationships between concepts (e.g., via shared claims, semantic similarity). It can suggest or automatically add "Related Concepts" sections to Tier 3 pages, creating `(:Concept)-[:RELATED_TO]->(:Concept)` edges in the graph.
    * **LlamaIndex `KnowledgeGraphIndex`:** This serves as the underlying structure, with agents adding/updating nodes (files, blocks, claims with quality attributes, sentences, concepts) and edges using the rich semantic relationships defined in the Claim Quality Schema & Knowledge Graph Ontology (see section IV). The Knowledge Graph also facilitates complex structural queries to guide the linking process.

---

## IV. Claim Quality Schema & Knowledge Graph Ontology

To ensure the "well-foundedness" of claims is explicit and machine-verifiable, aclarai adopts a schema inspired by Claimify.

### A. `Claim` Node Properties

Each `(:Claim)` node in the Knowledge Graph includes the following properties derived from Claimify principles:

| Property                     | Type   | Description                                                                                                                                                                                                                            | Claimify Principle    |
| ---------------------------- | ------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------- |
| `text`                       | String | The textual content of the claim.                                                                                                                                                                                                      |                       |
| `entailed_score`             | Float  | Confidence score (e.g., NLI score ≥ 0.9) that the source sentence logically implies the claim.                                                                                                                                        | Entailed              |
| `coverage_score`             | Float  | Score indicating how well the claim retains all crucial facts and information from the source sentence, ensuring no essential details are lost.                                                                                        | Coverage              |
| `decontextualization_score`  | Float  | Score measuring how well the claim can be understood independently, without additional context. High scores indicate the claim resolves pronouns, includes necessary qualifiers (time, location, scope), and remains meaningful in isolation. | Decontextualization   |
| `claim_id`                   | String | A unique identifier for the claim.                                                                                                                                                                                                     |                       |

### B. Key Relationship Types (Edges)

The following relationship types define how nodes are interconnected in the Knowledge Graph, replacing coarser, less descriptive types:

| Edge Type              | Start Node ➜ End Node                                     | Description                                                                                                                               |
| ---------------------- | --------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| **ORIGINATES\_FROM**   | `(:Claim) ➜ (:Block)` or `(:Sentence) ➜ (:Block)`         | Links a claim or sentence to its precise source segment (Markdown block) in a Tier 1 raw conversation file. Essential for provenance.       |
| **SUMMARIZED\_IN**     | `(:Claim) ➜ (:Summary)`                                   | Indicates that a claim appears (verbatim or paraphrased) in a Tier 2 conversation summary document.                                         |
| **SUPPORTS\_CONCEPT**  | `(:Claim) ➜ (:Concept)`                                   | The claim provides positive evidence for the concept and meets quality standards (high entailment, coverage, and decontextualization scores). Properties: `{strength: Float, entailed_score: Float, coverage_score: Float}`. |
| **CONTRADICTS\_CONCEPT**| `(:Claim) ➜ (:Concept)`                                   | The claim provides evidence that negates or refutes the concept and meets quality standards. Properties: `{strength: Float, entailed_score: Float, coverage_score: Float}`. |
| **MENTIONS\_CONCEPT**  | `(:Claim) ➜ (:Concept)`                                   | The claim mentions the concept but may not meet the full quality criteria for `SUPPORTS_CONCEPT` (e.g., lower decontextualization or coverage scores). |
| **ENTAILS\_CLAIM**     | `(:Claim) ➜ (:Claim)`                                     | A more general claim logically follows from another specific claim (identified via NLI).                                                    |
| **REFINES\_CLAIM**     | `(:Claim) ➜ (:Claim)`                                     | A claim provides more specific details (e.g., date, location, numbers) for another claim on the same topic.                               |
| **AMBIGUOUS\_WITH**    | `(:Sentence) ➜ (:Sentence)`                               | Used if claim extraction flags a sentence as having multiple unresolved interpretations; links these interpretations for potential review.       |
| **RELATED\_TO**        | `(:Concept) ➜ (:Concept)`                                 | A general relationship indicating two concepts are related, often discovered through graph analysis or LLM suggestions for cross-linking. |

### C. Edge Creation Rules & Confidence Weighting

*   **Guard-rails for Evidential Links:**
    *   A `SUPPORTS_CONCEPT` or `CONTRADICTS_CONCEPT` edge is created **only if** the source `(:Claim)` has high quality scores across all three metrics: `entailed_score ≥ 0.9`, `coverage_score ≥ 0.8`, and `decontextualization_score ≥ 0.8` (or similar high thresholds).
    *   If these quality standards are not met, but a relation still exists, the system downgrades the link to `MENTIONS_CONCEPT`.
*   **Confidence Weighting:**
    *   Edges like `SUPPORTS_CONCEPT` and `CONTRADICTS_CONCEPT` store the original claim's quality scores (`entailed_score`, `coverage_score`, `decontextualization_score`) along with the LLM-assigned `strength` of the relationship. This allows graph queries to weight evidence and rank claims based on their overall quality.
*   **Quality-Based Filtering:**
    *   Claims that fail to meet minimum quality thresholds are not promoted to the user-facing knowledge base, though they may be retained internally for debugging. This ensures that only well-founded, decontextualized claims with adequate coverage contribute to the structured knowledge graph and Obsidian vault.

This explicit schema for claims and relationships ensures that the "well-founded" nature of information is not a subjective label but a set of machine-verifiable metadata, making aclarai's knowledge graph more robust, auditable, and easier for downstream AI agents or human users to trust and consume.

---

## V. Obsidian Integration Philosophy

**aclarai** is designed to be a seamless extension of your Obsidian workflow:

* All connections between Tiers (1 to 2, 2 to 3, 3 to 3, 3 to 2) are explicitly created as standard `[[wikilinks]]` in your Markdown files.
* The internal Knowledge Graph acts as the intelligent "backend" that understands and manages these relationships, while Obsidian provides the intuitive, user-facing navigation and visualization.
* **aclarai** does not impose its own query interface; it empowers you to use Obsidian's native search, linking, and graph view to explore your newly organized knowledge base.

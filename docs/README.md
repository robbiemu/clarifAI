# 📚 ClarifAI Project Documentation: Your Compass

Welcome to the ClarifAI documentation hub! This file serves as your central point of orientation, guiding you through the various architectural decisions, technical specifications, and project plans that define ClarifAI.

Whether you're a new team member, a seasoned contributor, or just exploring the project, this guide will help you find the information you need quickly.

---

## 🧭 How to Use This Document

This document is organized into logical sections, mirroring the typical flow of understanding a software project. Each entry provides a brief description and a direct link to the relevant Markdown file.

*   **Project Vision & Product:** Understand *what* ClarifAI is and *why* it exists.
*   **Architecture & Design Principles:** Dive into *how* ClarifAI is built and the foundational technical decisions.
*   **Core Systems & Data Flow:** Explore the major components and the journey of data through the system.
*   **Agent & AI Logic (Deep Dives):** Get into the specifics of how ClarifAI's intelligent agents function.
*   **Development & Process:** Learn about our agile methodology and development workflows.

---

## 📝 Documentation Categories

### 🚀 1. Project Vision & Product

These documents articulate the core purpose, user value, and high-level technical direction of ClarifAI.

*   **[ClarifAI: Your AI for Conversational Clarity](docs/project/product_definition.md)**
    *   *Purpose:* The main product definition, outlining key features, value proposition, and the vision for ClarifAI.
*   **[ClarifAI: Technical Overview](docs/project/technical_overview.md)**
    *   *Purpose:* A high-level technical summary, covering core objectives, key components, technologies, and the overall agent workflow.
*   **[Selected User Stories for ClarifAI](docs/project/epic_1/epic.md)**
    *   *Purpose:* Defines the user needs and desired functionalities that drive development, serving as the foundation for sprint planning.
*   **[ClarifAI UX Overview](docs/project/ux_overview.md)**
    *   *Purpose:* Describes the user-facing structure and interaction points of ClarifAI, including import, review, and automation control.

### 🧱 2. Architecture & Design Principles

These documents detail the foundational architectural choices and cross-cutting design principles that govern ClarifAI's development.

*   **[ClarifAI Deployment Architecture (Docker Compose Edition)](docs/arch/architecture.md)**
    *   *Purpose:* Outlines the containerized architecture using Docker Compose for local and small-team deployments.
*   **[ClarifAI Configuration Panel Design](docs/arch/design_config_panel.md)**
    *   *Purpose:* Details the design for the configuration UI, including model settings, thresholds, and job controls.
*   **[ClarifAI Import Panel Design](docs/arch/design_import_panel.md)**
    *   *Purpose:* Describes the UI for ingesting conversations, format detection, and real-time feedback.
*   **[ClarifAI Review & Automation Status Panel Design](docs/arch/design_review_panel.md)**
    *   *Purpose:* Defines the UI for reviewing extracted claims, automation status, and basic controls.
*   **[Error Handling and Resilience Strategy](docs/arch/on-error-handling-and-resilience.md)**
    *   *Purpose:* Defines principles and mechanisms for robust error handling, retries, and graceful degradation across the system.
*   **[Logging Strategy](docs/arch/idea-logging.md)**
    *   *Purpose:* Outlines conventions for consistent logging across all services to aid debugging and operational insight.
*   **[LLM Interaction Strategy](docs/arch/on-llm_interaction_strategy.md)**
    *   *Purpose:* Guidelines for prompt management, response handling, and resource optimization when interacting with LLMs.
*   **[Obsidian File Handle Conflicts](docs/arch/on-filehandle_conflicts.md)**
    *   *Purpose:* Explains how ClarifAI handles concurrent file edits with Obsidian to prevent data corruption.

### ⚙️ 3. Core Systems & Data Flow

These documents specify the implementation details of core services and how data flows and is stored within ClarifAI.

*   **[ClarifAI Graph–Vault Sync Design](docs/arch/on-graph_vault_synchronization.md)**
    *   *Purpose:* Details the bidirectional synchronization between Obsidian Markdown files and the Neo4j knowledge graph.
*   **[Skeleton for the Pluggable Format Conversion System](docs/arch/on-pluggable_formats.md)**
    *   *Purpose:* Defines the architecture for extending ClarifAI with new input file format converters.
*   **[Vector Store Summary (Approved)](docs/arch/on-vector_stores.md)**
    *   *Purpose:* Summarizes the purpose and usage of various vector tables (`utterances`, `concept_candidates`, `concepts`) in ClarifAI.
*   **[Neo4j Interaction Strategy for ClarifAI](docs/arch/idea-neo4J-ineteraction.md)**
    *   *Purpose:* Outlines methods for interacting with Neo4j, including direct Cypher queries and LlamaIndex abstractions.
*   **[Vault Layout and Document Type Inference](docs/arch/on-vault_layout_and_type_inference.md)**
    *   *Purpose:* Explains how ClarifAI detects document types (Tier 1, 2, 3) via content markers, allowing flexible vault structures.

### 🧠 4. Agent & AI Logic (Deep Dives)

These documents explain the intricate workings of ClarifAI's intelligent agents and their underlying AI logic.

*   **[Claim Generation Walkthrough](docs/arch/on-claim_generation.md)**
    *   *Purpose:* Provides a step-by-step example of how conversational turns are processed into atomic claims.
*   **[Evaluation Roles](docs/arch/on-evaluation_agents.md)**
    *   *Purpose:* Defines the `entailment`, `coverage`, and `decontextualization` evaluation agents and their role in assessing claim quality.
*   **[Linking Claims to Concepts](docs/arch/on-linking_claims_to_concepts.md)**
    *   *Purpose:* Details how claims are linked to concepts using LLM-based classification.
*   **[Noun Phrase Extraction Tooling](docs/arch/on-noun_phrase_extraction.md)**
    *   *Purpose:* Explains the tools and methods used for extracting noun phrases from claims and summaries.
*   **[Concept Creation and Drift Handling (Initial Strategy)](docs/arch/on-concepts.md)**
    *   *Purpose:* Describes how concepts are identified, created, and managed, including deduplication via `hnswlib`.
*   **[Refreshing Concept Embeddings Job](docs/arch/on-refreshing_concept_embeddings.md)**
    *   *Purpose:* Outlines the scheduled job for updating concept embeddings based on changes in Tier 3 Markdown files.
*   **[Tier 3 Concept RAG Workflow Design](docs/arch/on-RAG_workflow.md)**
    *   *Purpose:* Describes the Retrieval-Augmented Generation (RAG) process for creating structured concept pages.
*   **[Sentence Splitting Strategy for Claimify Input](docs/arch/on-sentence_splitting.md)**
    *   *Purpose:* Details how conversational turns are segmented into coherent units for the Claimify pipeline.
*   **[On Writing Vault Documents](docs/arch/on-writing_vault_documents.md)**
    *   *Purpose:* Defines the output formats and agent responsibilities for all Markdown documents written to the vault.

### 🗓️ 5. Development & Process

These documents cover our agile development process, sprint plans, and setup instructions.

*   **[Sprint Plan for POC (Epic 1)](docs/project/epic_1/sprint_plan.md)**
    *   *Purpose:* The detailed breakdown of tasks for each sprint, providing the roadmap for the Proof of Concept.
    *   *Note:* Individual sprint task documents (e.g., `sprint_1-Build_Docker_Compose_stack.md`, `sprint_2-Create_Tier_1_Markdown.md`, etc.) are linked within the `sprint_plan.md` for granular details of each task.

---

### 💡 Additional Technical Notes

*   **[Create Tier 1 Markdown files with `clarifai:id` comments and Obsidian `^anchors`](docs/arch/idea-creating_tier1_documents.md)**
*   **[Implement Fallback Plugin (LLM Agent)](docs/arch/idea-default_plugin_task.md)**
*   **[Embed utterances and save vectors to Postgres](docs/arch/idea-embedding_in_vectordb.md)**
*   **[Gradio does support streaming — within its model](docs/arch/idea-front_end_ui_scaffolding.md)**
*   **[Configuring `PGVectorStore` to Use a Custom BERT Model for Embeddings in LlamaIndex](docs/arch/idea-sketch_how_to_use_a_BERT_model_with_llamaindex.md)**

---

## 🤝 Contributing to Documentation

This documentation is a living asset. If you find errors, omissions, or areas that could be clearer, please feel free to:

1.  **Open an Issue:** Describe the problem or suggestion.
2.  **Submit a Pull Request:** Directly contribute your improvements.

Your contributions help make ClarifAI better for everyone!
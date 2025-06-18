# 📚 aclarai Project Documentation: Your Compass

Welcome to the aclarai documentation hub! This file serves as your central point of orientation, guiding you through the various architectural decisions, technical specifications, and project plans that define aclarai.

Whether you're a new team member, a seasoned contributor, or just exploring the project, this guide will help you find the information you need quickly.

---

## 📖 Documentation Philosophy: Finding the Right Document

To help you find information efficiently, our documentation is organized into distinct categories. Understanding their purpose will help you locate the right document for your needs.

| Category | Purpose | Answers the Question... | Example |
| :--- | :--- | :--- | :--- |
| **`docs/arch`** | **Why?** (Architectural Decisions) | "Why was it built this way?" | [`on-vector_stores.md`](./arch/on-vector_stores.md) explains the rationale for our vector database choices. |
| **`docs/components`**| **What?** (System Overviews) | "What does this system do?" | [`embedding_system.md`](./components/embedding_system.md) provides a high-level summary of the embedding pipeline. |
| **`docs/guides`** | **How does it work?** (Reference) | "What are my options for X?" | [`embedding_models_guide.md`](./guides/embedding_models_guide.md) is a reference for all supported embedding models. |
| **`docs/tutorials`**| **How do I do it?** (Instruction) | "How do I use X to achieve a goal?" | [`embedding_system_tutorial.md`](./tutorials/embedding_system_tutorial.md) is a step-by-step recipe for embedding a document. |

---

## 📝 Documentation Categories

### 🚀 1. Project Vision & Product

These documents articulate the core purpose, user value, and high-level technical direction of aclarai.

*   **[aclarai: Your AI for Conversational Clarity](./project/product_definition.md)**
*   **[aclarai: Technical Overview](./project/technical_overview.md)**
*   **[Selected User Stories for aclarai](./project/epic_1/epic.md)**
*   **[aclarai UX Overview](./project/ux_overview.md)**

### 🧩 2. Core Component Overviews (The "What")

These documents provide high-level summaries of aclarai's major systems. They are the best starting point for understanding what each component does.

*   **[Block Syncing Loop](./components/block_syncing_loop.md)**
*   **[Claimify Pipeline System](./components/claimify_pipeline_system.md)**
*   **[Embedding System](./components/embedding_system.md)**
*   **[Graph System (Neo4j)](./components/graph_system.md)**
*   **[Import System](./components/import_system.md)**
*   **[Scheduler System](./components/scheduler_system.md)**
*   **[UI System (Gradio)](./components/ui_system.md)**
*   **[Vault Watcher System](./components/vault_watcher_system.md)**

### 🧱 3. Architecture & Design Principles (The "Why")

These documents detail the foundational architectural choices and cross-cutting design principles that govern development.

*   **[aclarai Deployment Architecture (Docker Compose Edition)](./arch/architecture.md)**
*   **[UI Design Docs](./arch/design_config_panel.md)** (Consolidated from `design_config_panel`, `design_import_panel`, etc. or list them individually)
*   **[Error Handling and Resilience Strategy](./arch/on-error-handling-and-resilience.md)**
*   **[Logging Strategy](./arch/idea-logging.md)**
*   **[LLM Interaction Strategy](./arch/on-llm_interaction_strategy.md)**
*   **[Obsidian File Handle Conflicts](./arch/on-filehandle_conflicts.md)**

### ⚙️ 4. Core Systems & Data Flow

These documents specify the implementation details of core services and how data flows and is stored.

*   **[aclarai Graph–Vault Sync Design](./arch/on-graph_vault_synchronization.md)**
*   **[Pluggable Format Conversion System](./arch/on-pluggable_formats.md)**
*   **[Vector Store Summary](./arch/on-vector_stores.md)**
*   **[Neo4j Interaction Strategy](./arch/idea-neo4J-ineteraction.md)**
*   **[Vault Layout and Document Type Inference](./arch/on-vault_layout_and_type_inference.md)**

### 🧠 5. Agent & AI Logic (Deep Dives)

These documents explain the intricate workings of aclarai's intelligent agents and their underlying AI logic.

*   **[Claim Generation Walkthrough](./arch/on-claim_generation.md)**
*   **[Concept Creation and Drift Handling](./arch/on-concepts.md)**
*   **[Evaluation Roles (Agents)](./arch/on-evaluation_agents.md)**
*   **[Linking Claims to Concepts](./arch/on-linking_claims_to_concepts.md)**
*   **[Tier 3 Concept RAG Workflow Design](./arch/on-RAG_workflow.md)**
*   ...and other AI logic docs.

### 📚 6. Guides & Tutorials (The "How")

These documents provide practical instructions and comprehensive references for using, configuring, and contributing to aclarai.

*   **Guides (Reference Manuals):**
    *   **[Claimify Pipeline Guide](./guides/claimify_pipeline_guide.md)**
    *   **[Embedding Models Guide](./guides/embedding_models_guide.md)**
    *   **[Scheduler Setup Guide](./guides/scheduler_setup_guide.md)**
*   **Tutorials (Step-by-Step Lessons):**
    *   **[End-to-End Claimify Tutorial](./tutorials/claimify_integration_tutorial.md)**
    *   **[Importing Your First Conversation](./tutorials/tier1_import_tutorial.md)**
    *   **[Working with the Neo4j Graph](./tutorials/neo4j_graph_tutorial.md)**

### 🗓️ 7. Development & Process

These documents cover our agile development process and sprint plans.

*   **[Sprint Plan for POC (Epic 1)](./project/epic_1/sprint_plan.md)**

---

## 🤝 Contributing to Documentation

This documentation is a living asset. If you find errors, omissions, or areas that could be clearer, please feel free to open an issue or submit a pull request. Your contributions help make aclarai better for everyone
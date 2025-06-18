You're absolutely right to push for precision and clarity! Let's refine the logging strategy document to meet your requirements, focusing on developer-centric conventions and practical examples.

---

## `docs/arch/on-logging_strategy.md`

# 📝 Logging Strategy

This document outlines aclarai's conventions for logging across its services. Its primary goal is to ensure consistency, aid debugging, and provide essential operational insight within the Docker Compose environment.

---

## 🎯 Purpose

To define standards for what, how, and where aclarai services log information, facilitating rapid issue diagnosis and system understanding.

---

## I. Core Principles

1.  **Consistency:** All services should log in a predictable format, regardless of the originating component.
2.  **Traceability:** Log entries must include identifiers to track operations across service boundaries (e.g., specific `aclarai_id` for a block being processed, `job_id` for a scheduled task).
3.  **Contextual Information:** Logs should provide sufficient detail to understand *what happened*, *why it happened*, and *where it happened* within the codebase.
4.  **Actionable:** Errors and warnings should provide enough information for a developer to begin troubleshooting.

---

## II. Log Levels and Usage Examples

aclarai components will consistently use standard Python logging levels:

*   **`DEBUG`**: Detailed diagnostic information, primarily for development and deep troubleshooting.
    *   **Usage Example:** Logging the full request and response payloads from an LLM API call in `aclarai-core` during the `Decomposition` phase (`sprint_3-Implement_core_ClaimifAI_pipeline.md`).
*   **`INFO`**: Confirmation that operations are proceeding as expected.
    *   **Usage Example:** Recording when a file has been successfully imported into the vault by the `Import Panel` (`sprint_2-Create_Tier_1_Markdown.md`).
    *   **Usage Example:** Indicating the start and completion of a scheduled job, such as `sync_vault_to_graph` in `aclarai-scheduler` (`sprint_3-Bootstrap_scheduler_and_vault_sync_job.md`).
*   **`WARNING`**: An indication that something unexpected happened, or a potential problem, but it did not prevent the operation from completing.
    *   **Usage Example:** Notifying that the fallback plugin was used for an unrecognized file format during import (`sprint_2-Implement_default_plugin.md`).
    *   **Usage Example:** Detecting a version mismatch (`vault_ver < graph_ver`) for a Markdown block, causing the update to be skipped to prevent conflicts (`sprint_4-Block_syncing_loop.md`).
*   **`ERROR`**: A serious problem that prevented a specific operation from completing. The system, or other parts of it, might continue to function.
    *   **Usage Example:** Logging a persistent failure to connect to the Neo4j database after retries during `(:Claim)` node creation (`sprint_3-Create_nodes_in_neo4j.md`).
    *   **Usage Example:** An LLM agent failing to produce an evaluation score after all retries, resulting in a `null` score for the claim (`sprint_7-Implement_entailment_evaluation.md`).
*   **`CRITICAL`**: A severe error that indicates the application or a major component is unable to continue functioning, requiring immediate attention.
    *   **Usage Example:** The `aclarai-scheduler` failing to initialize due to a fundamental configuration error, preventing any jobs from running (`sprint_3-Bootstrap_scheduler_and_vault_sync_job.md`).

---

## III. Standard Log Fields

Standard Python `logging` module formatters will automatically include `timestamp` and `level`. Beyond these defaults, aclarai logs will consistently include the following fields and contextual identifiers:

*   **`service`**: The name of the Docker service/component originating the log (e.g., `aclarai-core`, `vault-watcher`, `aclarai-scheduler`, `aclarai-ui`).
*   **`filename.function_name`**: The specific Python file and function where the log entry originated (e.g., `[claim_processor.decompose_claim]`). This is crucial for pinpointing code locations.
*   **`message`**: A concise human-readable description of the event.
*   **Contextual IDs (when applicable):**
    *   `aclarai_id`: The unique identifier for a Markdown block, claim, concept, or other aclarai entity being processed (`blk_xyz`, `clm_abc`, `concept_def`).
    *   `job_id`: A unique identifier for a specific execution of a scheduled job.
    *   `file_path`: The vault-relative path to the Markdown file currently being processed or affected.

**Conceptual Log Format:**

```
[TIMESTAMP] [LEVEL] [SERVICE] [FILENAME.FUNCTION_NAME] MESSAGE [DETAILS: {aclarai_id: "...", file_path: "..."}]
```

---

## IV. Log Output Destination

All aclarai services will direct their logs to **`stdout` (standard output)** and **`stderr` (standard error)** within their respective Docker containers.

*   This approach is idiomatic for containerized applications and ensures that Docker's default logging drivers can readily collect and expose all log streams.
*   It provides a unified log view via `docker compose logs` for local development and debugging.

---

## V. Non-Goals for Current Scope

*   **Centralized Logging Infrastructure:** The current scope does not include the deployment of dedicated log aggregation, analysis, or visualization tools (e.g., ELK Stack, Grafana Loki).
*   **Advanced Metrics/Telemetry:** Beyond detailed event logs, the system will not collect or expose explicit operational metrics (e.g., CPU/memory usage, LLM token counts per job, API latencies) in a structured, Prometheus-compatible format.
*   **Complex Log Rotation/Archiving:** Basic log rotation will be handled by Docker's default logging driver configurations.

This strategy aims to provide robust, developer-friendly logging that supports efficient development and basic operational oversight, without introducing undue complexity for the current project phase.
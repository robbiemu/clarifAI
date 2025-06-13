# ClarifAI UI System

This document provides a comprehensive overview of the ClarifAI User Interface (UI) system, which is built using the Gradio framework.

## Overview

The ClarifAI UI provides a user-facing interface for interacting with the system's core functionalities, including data import, configuration management, and status monitoring. The UI is designed to be lightweight, intuitive, and seamlessly integrated into the Python-based monorepo, allowing for rapid development and direct interaction with backend services.

## Architecture

-   **Framework:** The entire UI is built using **Gradio**, which allows for the creation of web-based interfaces purely in Python.
-   **Integration:** The UI service runs in its own Docker container but interacts directly with other services (like `clarifai-core`) by calling functions from the `clarifai-shared` library. This avoids the need for an intermediate REST API, simplifying development.
-   **State Management:** UI state (like the live import queue) is managed within the Gradio application using `gr.State` objects, ensuring a responsive user experience.

## UI Panels

The ClarifAI UI is composed of several distinct panels, each designed for a specific purpose.

### 1. Import Panel
-   **Purpose:** To ingest conversation files from various sources.
-   **Features:**
    -   A file picker supporting drag-and-drop for formats like `.json`, `.csv`, and `.txt`.
    -   Automatic format detection using the pluggable import system.
    -   A "Live Import Queue" that provides real-time feedback on the status of each file (Imported, Failed, Fallback, Skipped).
    -   A post-import summary with statistics and links to the generated Tier 1 files.
-   **Design Document:** [ClarifAI Import Panel Design](../../docs/arch/design_import_panel.md)

### 2. Review & Automation Status Panel
-   **Purpose:** To review extracted data and manage system automation.
-   **Features (Planned):**
    -   A file/block index to view processing status.
    -   A detailed view for inspecting individual claims and their evaluation scores.
    *   A global "Pause/Resume Automation" control.
    *   A log preview for scheduled jobs.
-   **Design Document:** [ClarifAI Review & Automation Status Panel Design](../../docs/arch/design_review_panel.md)

### 3. Configuration Panel
-   **Purpose:** To allow users to tune system parameters and agent behavior.
-   **Features (Planned):**
    -   Controls for selecting LLM and embedding models for different tasks.
    -   Sliders and inputs for adjusting processing thresholds (e.g., similarity scores).
    -   Configuration for scheduled jobs (e.g., enabling/disabling, setting cron schedules).
-   **Design Document:** [ClarifAI Configuration Panel Design](../../docs/arch/design_config_panel.md)


## Development & Testing

### Running the Service

The UI service can be run standalone for development and testing.

**1. Using Docker Compose (Recommended):**

The simplest way to run the entire stack, including the UI, is with Docker Compose from the project root:
```bash
docker compose up -d clarifai-ui
```
The UI will be available at `http://localhost:7860`.

**2. Running Locally for Development:**

To run the UI service directly on your host machine for faster development iterations:
```bash
# Navigate to the service directory from the project root
cd services/clarifai-ui

# Install dependencies (if not already installed via the monorepo setup)
pip install -e .

# Run the main application
python -m clarifai_ui.main
```

### Simulation vs. Integration

-   **Initial Implementation:** The UI service was initially scaffolded with **simulated backend functions** (e.g., `simulate_plugin_orchestrator`). This allows for frontend development and testing before the real backend logic is complete.
-   **Full Integration:** As backend components are developed, these simulations are replaced with direct calls to the real import orchestrator and other functions in the `clarifai-shared` library.

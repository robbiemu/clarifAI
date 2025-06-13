# ClarifAI Core

This service is the main processing engine for the ClarifAI project. It handles ingestion of conversational data, extraction of claims, generation of summaries, linking concepts, and interacts with the vector store and knowledge graph.

## Installation Scripts

The `install/` directory contains scripts that are executed during the Docker build process to set up the service environment. This content is described here because its function is not immediately apparent from the service's primary source code.

- `install/install_prompts.py`

  This command-line utility is responsible for installing the default LLM prompt templates into the user-configurable `/settings/prompts` directory.

  **Purpose:**

  1.  **User Customization:** It copies the built-in prompt templates (from the `shared/clarifai_shared/prompts/` library) into the `/settings` volume. This exposes the prompts to the user, allowing them to inspect and customize agent behavior without modifying the core codebase.
  2.  **Docker Environment Setup:** It ensures that when the service starts in a clean Docker environment, the necessary prompt files are present in the mounted `/settings/prompts` volume, making the service ready to run immediately.

  This script is called from the `Dockerfile` during the image build process:

  ```dockerfile
  # From services/clarifai-core/Dockerfile
  RUN mkdir -p /settings/prompts && python install/install_prompts.py --all --prompts-dir /settings/prompts
  ```
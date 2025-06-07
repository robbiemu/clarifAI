# ClarifAI Vault Directory

This directory serves as the shared vault for Obsidian-style Markdown files that ClarifAI processes.

## Structure

- This directory is mounted as `/vault` in the Docker containers
- Files placed here will be watched by the `vault-watcher` service
- The `clarifai-core` service processes files from this directory
- The `scheduler` service performs periodic maintenance on this directory

## Usage

1. Place your Markdown files in this directory
2. The `vault-watcher` service will detect changes and emit dirty block IDs
3. The `clarifai-core` service will process the files for claim extraction, summarization, and concept linking
4. The `scheduler` service will run periodic jobs for concept hygiene and vault sync

## Important Notes

- Ensure this directory is writable by the Docker containers
- Files are processed atomically using `.tmp` → `rename` operations
- The system uses `clarifai:id` and `ver=` markers to track file versions
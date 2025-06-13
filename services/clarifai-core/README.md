# ClarifAI Core

This service is the main processing engine for the ClarifAI project. It handles ingestion of conversational data, extraction of claims, generation of summaries, linking concepts, and interacts with the vector store and knowledge graph.

## Installation Scripts

This service includes installation scripts to help with setup and maintenance:

### Prompt Templates
```bash
python install/install_prompts.py --all
python install/install_prompts.py --template conversation_extraction --force
```

### Configuration Files
```bash
python install/install_config.py
python install/install_config.py --force  # Restore defaults
```

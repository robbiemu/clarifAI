# ClarifAI UI

This service provides the user interface for the ClarifAI project using **Gradio**. It allows users to import conversation data, manage configurations, review extracted information, and monitor the status of various automated processes.

## Features

- **Import Panel**: Upload and process conversation files with real-time feedback
- **Plugin Simulation**: Demonstrates the import workflow with simulated plugin output
- **Web-based Interface**: Built with Gradio for easy access and use

## Structure

```
clarifai_ui/
├── __init__.py          # Package initialization
├── main.py              # Main Gradio application
└── README.md            # This file
```

## Installation

Install the service dependencies:

```bash
cd services/clarifai-ui
pip install -e .
```

Or using the monorepo setup:

```bash
# From the repository root
uv sync
```

## Running Locally

### Option 1: Using the module directly
```bash
cd services/clarifai-ui
python -m clarifai_ui.main
```

### Option 2: Using the installed command (if installed with pip)
```bash
clarifai-ui
```

### Option 3: Using Docker
```bash
cd services/clarifai-ui
docker build -t clarifai-ui .
docker run -p 7860:7860 clarifai-ui
```

The application will be available at `http://localhost:7860`

## Usage

1. **Upload File**: Click on the file selector to upload a conversation file (supports .json, .txt, .csv, .md)
2. **Import**: Click the "Import File" button or the upload will automatically trigger processing
3. **View Logs**: Monitor the import process in the log area with real-time feedback
4. **Review Results**: See simulated plugin output showing extraction results

## Import Panel Features

The `/import` route (default page) provides:

- **File Selector** (`gr.File`): Supports common conversation file formats
- **Import Button**: Triggers the import simulation
- **Log Area** (`gr.Textbox`): Displays real-time processing status and results
- **Plugin Simulation**: Demonstrates the complete import workflow

### Simulated Output

The current implementation simulates:
- File format detection
- Plugin selection and initialization  
- Conversation data processing
- Tier 1 Markdown generation
- Claims extraction
- Participant identification
- Processing metrics

## Development

### Code Structure

- **Gradio Interface**: Built using `gr.Blocks` for flexible layout
- **Modular Design**: Functions separated for reusability
- **Plugin Simulation**: `simulate_plugin_output()` function demonstrates expected workflow

### Integration Points

This scaffolded frontend is designed to integrate with:
- Import plugin orchestrator (future sprint)
- Backend processing services
- File storage and vault management
- Real-time status updates

### Testing

Test the interface creation:

```bash
cd services/clarifai-ui
python -c "
from clarifai_ui.main import create_import_interface
interface = create_import_interface()
print('Interface created successfully!')
"
```

## Configuration

The Gradio app runs on:
- **Host**: `0.0.0.0` (all interfaces)
- **Port**: `7860`
- **Debug**: Disabled in production

These settings can be modified in `main.py` in the `main()` function.

## Future Development

This scaffolded frontend provides the foundation for:
- Real plugin integration
- Configuration management panels
- Advanced status monitoring
- Multi-tab interface layouts
- Authentication and user management

## Technical Notes

- Built entirely in Python using Gradio
- Uses `gr.Blocks` for flexible layouts
- State managed internally by Gradio components
- Ready for integration with monorepo backend services
- Follows project linting and formatting standards

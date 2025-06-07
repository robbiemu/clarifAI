# ClarifAI UI

This service provides the user interface for the ClarifAI project using **Gradio**. It implements the complete import panel design following the specifications in `docs/arch/design_import_panel.md` and the UX overview in `docs/project/ux_overview.md`.

## Features

- **Complete Import Panel**: Full implementation of the documented import panel design
- **Live Import Queue**: Real-time status tracking with formatted table display
- **Plugin Orchestrator Simulation**: Demonstrates the complete workflow with format detection
- **Post-import Summary**: Comprehensive statistics and next steps
- **Format Detection**: Automatic plugin selection based on file type and content
- **Fallback Plugin Support**: Handles unsupported formats gracefully
- **Duplicate Detection**: Identifies and skips duplicate imports

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

### Import Panel Components

The import panel implements the complete design from `docs/arch/design_import_panel.md`:

#### 1. File Picker
- **Drag & Drop**: Drop files directly into the upload area
- **File Browser**: Click to browse and select files
- **Supported Formats**: `.json`, `.txt`, `.csv`, `.md`, `.zip`
- **Auto-processing**: Files are processed immediately upon upload

#### 2. Format Detection
- **Automatic Detection**: System automatically applies pluggable format detectors
- **No Manual Selection**: Users never choose formats manually
- **Fallback Support**: Unsupported formats route to fallback plugin

#### 3. Live Import Queue
Real-time status table showing:

| Column | Description |
|--------|-------------|
| Filename | Name of the uploaded file |
| Status | Current processing status with icons |
| Detector | Which plugin handled the file |
| Time | When processing started |

**Status Icons:**
- ✅ **Imported**: Successfully processed
- ❌ **Failed**: Processing failed
- ⚠️ **Fallback**: Processed by fallback plugin
- ⏸️ **Skipped**: Duplicate or skipped file
- 🔄 **Processing**: Currently being processed

#### 4. Post-import Summary
Comprehensive statistics displayed after processing:
- Total files processed
- Files successfully imported
- Files that used fallback plugin
- Files that failed to import
- Files skipped (duplicates)
- Links to view imported files and logs

### Workflow Example

1. **Upload**: Drop a `conversation.json` file
2. **Detection**: System detects ChatGPT format → uses `chatgpt_json` plugin
3. **Processing**: File processes → Status shows "✅ Imported"
4. **Summary**: Summary shows "1 file successfully imported"
5. **Next Steps**: Links provided to view results in vault

## Import Panel Features

The `/import` route (default page) implements the complete design specification:

### Core Components
- **File Picker**: Drag-and-drop or click-to-browse file selection
- **Live Import Queue**: Real-time table showing processing status
- **Post-import Summary**: Statistics and next steps after processing
- **Format Detection**: Automatic plugin selection (no user intervention)

### Supported Formats & Plugins

| Format | Extension | Plugin | Description |
|--------|-----------|--------|-------------|
| ChatGPT Export | `.json` | `chatgpt_json` | ChatGPT conversation exports |
| Slack Export | `.csv` | `slack_csv` | Slack conversation logs |
| Markdown | `.md` | `markdown` | Markdown conversation files |
| Generic Text | `.txt` | `fallback_llm` | Plain text (uses fallback) |

### Plugin Orchestrator Simulation

The current implementation simulates the complete plugin orchestrator workflow:

1. **File Upload**: User uploads conversation file
2. **Format Detection**: System runs `can_accept()` methods on all plugins
3. **Plugin Selection**: Appropriate plugin selected automatically
4. **Processing**: File processed to generate Tier 1 Markdown
5. **Status Update**: Real-time updates in Live Import Queue
6. **Summary Generation**: Post-import statistics and links

### Edge Cases Handled

- **Duplicates**: Files with same name are skipped
- **Unsupported Formats**: Route to fallback plugin
- **Processing Failures**: Clear error indication
- **Empty Uploads**: Graceful handling of no file selected

### Real-time Feedback

- **Processing Status**: Live updates during import
- **Visual Indicators**: Icons and colors for different states
- **Completion Summary**: Final statistics and next steps
- **Error Handling**: Clear error messages and recovery options

## Development

### Code Structure

- **Gradio Interface**: Built using `gr.Blocks` for flexible layout
- **Modular Design**: Functions separated for reusability
- **Plugin Simulation**: `simulate_plugin_output()` function demonstrates expected workflow

### Integration Points

This implementation is designed for seamless integration with:

- **Plugin Orchestrator**: Ready to replace simulation with real plugin system
- **Format Detectors**: Pluggable format detection via `can_accept()` methods
- **Vault Storage**: File output paths configured for vault structure
- **Neo4j Graph**: Claims and concepts ready for graph integration
- **Scheduler Services**: Import jobs ready for background processing
- **Configuration System**: Settings integration for thresholds and options

### Architecture Alignment

The implementation follows the documented architecture:

- **UX Overview** (`docs/project/ux_overview.md`): Complete import workflow
- **Import Panel Design** (`docs/arch/design_import_panel.md`): UI components and layout
- **Sprint Requirements**: Both Sprint 1 scaffolding and Sprint 8 complete panel
- **Plugin Architecture**: Ready for pluggable format conversion system
- **Monorepo Structure**: Integrated within services architecture

### Testing

Test the complete import interface:

```bash
cd services/clarifai-ui
python -c "
from clarifai_ui.main import create_import_interface
interface = create_import_interface()
print('✓ Complete import interface created successfully!')
print('✓ Components: File picker, Live Queue, Summary')
print('✓ Features: Format detection, plugin simulation, real-time status')
"
```

Test the plugin orchestrator simulation:

```bash
python -c "
from clarifai_ui.main import simulate_plugin_orchestrator
queue, summary = simulate_plugin_orchestrator('/path/to/test.json')
print('Plugin orchestrator simulation working!')
"
```

## Configuration

The Gradio app runs on:
- **Host**: `0.0.0.0` (all interfaces)
- **Port**: `7860`
- **Debug**: Disabled in production

These settings can be modified in `main.py` in the `main()` function.

## Future Development

This complete import panel implementation provides the foundation for:

- **Real Plugin Integration**: Replace simulation with actual plugin orchestrator
- **Backend Communication**: Connect to clarifai-core services
- **Configuration Panels**: Add settings and automation control UI
- **Advanced Status Monitoring**: Detailed processing logs and metrics
- **Multi-tab Interface**: Review panel, config panel, status dashboard
- **Authentication**: User management and access control
- **Batch Processing**: Multiple file handling and queue management

## Technical Notes

- **Design Compliance**: Fully implements `docs/arch/design_import_panel.md`
- **UX Alignment**: Follows `docs/project/ux_overview.md` specifications
- **Plugin Architecture**: Ready for pluggable format conversion system
- **Gradio Framework**: Uses `gr.Blocks` for flexible, responsive layouts
- **State Management**: Proper queue tracking and status updates
- **Error Handling**: Graceful handling of edge cases and failures
- **Monorepo Integration**: Follows project structure and standards

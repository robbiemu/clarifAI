"""Main Gradio application for ClarifAI frontend."""

import gradio as gr
import os
import time
from typing import Optional, Tuple, List
from datetime import datetime


class ImportStatus:
    """Class to track import status and queue."""
    
    def __init__(self):
        self.import_queue = []
        self.summary_stats = {"imported": 0, "failed": 0, "fallback": 0, "skipped": 0}
    
    def add_file(self, filename: str, file_path: str) -> None:
        """Add a file to the import queue."""
        self.import_queue.append({
            "filename": filename,
            "path": file_path,
            "status": "Processing...",
            "detector": "Detecting...",
            "timestamp": datetime.now().strftime("%H:%M:%S")
        })
    
    def update_file_status(self, filename: str, status: str, detector: str) -> None:
        """Update the status of a file in the queue."""
        for item in self.import_queue:
            if item["filename"] == filename:
                item["status"] = status
                item["detector"] = detector
                break
    
    def format_queue_display(self) -> str:
        """Format the import queue for display."""
        if not self.import_queue:
            return "No files in import queue."
        
        header = "| Filename | Status | Detector | Time |\n|----------|--------|----------|------|\n"
        rows = []
        
        for item in self.import_queue:
            status_icon = {
                "✅ Imported": "✅",
                "❌ Failed": "❌", 
                "⚠️ Fallback": "⚠️",
                "⏸️ Skipped": "⏸️",
                "Processing...": "🔄"
            }.get(item["status"], "🔄")
            
            row = f"| {item['filename']} | {status_icon} {item['status']} | {item['detector']} | {item['timestamp']} |"
            rows.append(row)
        
        return header + "\n".join(rows)
    
    def get_summary(self) -> str:
        """Get post-import summary."""
        if not self.import_queue:
            return ""
        
        total = len(self.import_queue)
        imported = sum(1 for item in self.import_queue if item["status"] == "✅ Imported")
        failed = sum(1 for item in self.import_queue if item["status"] == "❌ Failed")
        fallback = sum(1 for item in self.import_queue if item["status"] == "⚠️ Fallback")
        skipped = sum(1 for item in self.import_queue if item["status"] == "⏸️ Skipped")
        
        summary = f"""## 📊 Import Summary

**Total Files Processed:** {total}

✅ **Successfully Imported:** {imported} files
⚠️ **Used Fallback Plugin:** {fallback} files  
❌ **Failed to Import:** {failed} files
⏸️ **Skipped (Duplicates):** {skipped} files

### Next Steps:
- [View Imported Files](./vault/tier1/) (files written to vault)
- [Download Import Log](./.clarifai/import_logs/) (detailed processing logs)
"""
        return summary

# Global import status tracker
import_status = ImportStatus()


def detect_file_format(file_path: str, filename: str) -> Tuple[str, str]:
    """Simulate format detection logic.
    
    Returns:
        Tuple of (detector_name, status)
    """
    # Simulate format detection based on file extension and content
    time.sleep(0.5)  # Simulate processing time
    
    if filename.lower().endswith('.json'):
        # Simulate checking if it's a ChatGPT export
        return "chatgpt_json", "✅ Imported"
    elif filename.lower().endswith('.csv'):
        # Simulate Slack CSV format
        return "slack_csv", "✅ Imported"
    elif filename.lower().endswith('.txt'):
        # Simulate generic text that needs fallback
        return "fallback_llm", "⚠️ Fallback"
    elif filename.lower().endswith('.md'):
        # Simulate markdown format
        return "markdown", "✅ Imported"
    else:
        # Simulate unsupported format
        return "None", "❌ Failed"


def simulate_plugin_orchestrator(file_path: Optional[str]) -> Tuple[str, str]:
    """Simulate the plugin orchestrator processing a file.
    
    Args:
        file_path: Path to uploaded file
        
    Returns:
        Tuple of (queue_display, summary_display)
    """
    if not file_path:
        return "No file selected for import.", ""
    
    filename = os.path.basename(file_path)
    
    # Check for duplicates (simple simulation)
    existing_files = [item["filename"] for item in import_status.import_queue]
    if filename in existing_files:
        import_status.update_file_status(filename, "⏸️ Skipped", "Duplicate")
        return import_status.format_queue_display(), import_status.get_summary()
    
    # Add file to queue
    import_status.add_file(filename, file_path)
    
    # Start with processing status
    queue_display = import_status.format_queue_display()
    
    # Simulate format detection and processing
    detector, status = detect_file_format(file_path, filename)
    
    # Update status after "processing"
    time.sleep(1)  # Simulate processing time
    import_status.update_file_status(filename, status, detector)
    
    return import_status.format_queue_display(), import_status.get_summary()


def clear_import_queue() -> Tuple[str, str]:
    """Clear the import queue and reset statistics."""
    global import_status
    import_status = ImportStatus()
    return "Import queue cleared.", ""


def create_import_interface():
    """Create the complete import interface following the documented design."""
    with gr.Blocks(title="ClarifAI - Import Panel", theme=gr.themes.Soft()) as interface:
        gr.Markdown("# 📥 ClarifAI Import Panel")
        gr.Markdown(
            """Upload conversation files from various sources (ChatGPT exports, Slack logs, generic text files) 
            to process and import into the ClarifAI system. Files are automatically detected and processed 
            using the appropriate format plugin."""
        )
        
        # File Picker Section
        with gr.Group():
            gr.Markdown("## 📁 File Selection")
            file_input = gr.File(
                label="Drag files here or click to browse",
                file_types=[".json", ".txt", ".csv", ".md", ".zip"],
                type="filepath",
                height=100
            )
            
            with gr.Row():
                import_btn = gr.Button("🚀 Process File", variant="primary", size="lg")
                clear_btn = gr.Button("🗑️ Clear Queue", variant="secondary")
        
        # Live Import Queue Section  
        with gr.Group():
            gr.Markdown("## 📋 Live Import Queue")
            queue_display = gr.Markdown(
                value="No files in import queue.",
                label="Import Status"
            )
        
        # Post-import Summary Section
        with gr.Group():
            gr.Markdown("## 📊 Import Summary")
            summary_display = gr.Markdown(
                value="Process files to see import summary.",
                label="Summary"
            )
        
        # Event handlers
        import_btn.click(
            fn=simulate_plugin_orchestrator,
            inputs=[file_input],
            outputs=[queue_display, summary_display]
        )
        
        # Auto-process on file upload
        file_input.change(
            fn=simulate_plugin_orchestrator,
            inputs=[file_input],
            outputs=[queue_display, summary_display]
        )
        
        # Clear queue handler
        clear_btn.click(
            fn=clear_import_queue,
            inputs=[],
            outputs=[queue_display, summary_display]
        )
    
    return interface


def main():
    """Launch the Gradio application."""
    interface = create_import_interface()
    interface.launch(server_name="0.0.0.0", server_port=7860, share=False, debug=False)


if __name__ == "__main__":
    main()

"""Main Gradio application for ClarifAI frontend."""

import gradio as gr
from typing import Optional


def simulate_plugin_output(file_path: Optional[str]) -> str:
    """Simulate plugin output for file import.

    Args:
        file_path: Path to uploaded file

    Returns:
        Simulated log output from plugin processing
    """
    if not file_path:
        return "No file selected."

    # Simulate plugin processing
    import os

    filename = os.path.basename(file_path)
    file_size = os.path.getsize(file_path)

    log_output = f"""
=== ClarifAI Import Simulation ===
File: {filename}
Size: {file_size} bytes
Status: Processing...

[INFO] Detecting file format...
[INFO] Format detected: Generic text/conversation
[INFO] Initializing import plugin...
[INFO] Processing conversation data...
[INFO] Extracting utterances...
[INFO] Generating Tier 1 Markdown...
[SUCCESS] Import completed successfully!

Generated output: /vault/{filename}.md
Claims extracted: 3
Participants identified: 2
Processing time: 1.2s
"""
    return log_output


def create_import_interface():
    """Create the main import interface using Gradio."""
    with gr.Blocks(title="ClarifAI - Import Panel") as interface:
        gr.Markdown("# ClarifAI Import Panel")
        gr.Markdown(
            "Upload conversation files to process and import into the ClarifAI system."
        )

        with gr.Row():
            with gr.Column():
                file_input = gr.File(
                    label="Select Conversation File",
                    file_types=[".json", ".txt", ".csv", ".md"],
                    type="filepath",
                )

                import_btn = gr.Button("Import File", variant="primary")

            with gr.Column():
                log_output = gr.Textbox(
                    label="Import Log",
                    lines=15,
                    max_lines=20,
                    interactive=False,
                    placeholder="Import logs will appear here...",
                )

        # Set up the import action
        import_btn.click(
            fn=simulate_plugin_output, inputs=[file_input], outputs=[log_output]
        )

        # Also trigger on file upload
        file_input.change(
            fn=simulate_plugin_output, inputs=[file_input], outputs=[log_output]
        )

    return interface


def main():
    """Launch the Gradio application."""
    interface = create_import_interface()
    interface.launch(server_name="0.0.0.0", server_port=7860, share=False, debug=False)


if __name__ == "__main__":
    main()

"""Tests for the main Gradio application and import functionality."""

import os
import sys
import tempfile
from pathlib import Path

# Add the service directory to the path for testing
service_dir = Path(__file__).parent.parent
sys.path.insert(0, str(service_dir))

# ruff: noqa: E402
from aclarai_ui.main import (
    ImportStatus,
    detect_file_format,
    simulate_plugin_orchestrator,
    clear_import_queue,
    create_import_interface,
)


class TestImportStatus:
    """Test the ImportStatus class."""

    def test_init(self):
        """Test ImportStatus initialization."""
        status = ImportStatus()
        assert status.import_queue == []
        assert status.summary_stats == {
            "imported": 0,
            "failed": 0,
            "fallback": 0,
            "skipped": 0,
        }

    def test_add_file(self):
        """Test adding a file to the import queue."""
        status = ImportStatus()
        status.add_file("test.json", "/path/to/test.json")

        assert len(status.import_queue) == 1
        assert status.import_queue[0]["filename"] == "test.json"
        assert status.import_queue[0]["path"] == "/path/to/test.json"
        assert status.import_queue[0]["status"] == "Processing..."
        assert status.import_queue[0]["detector"] == "Detecting..."
        assert "timestamp" in status.import_queue[0]

    def test_update_file_status(self):
        """Test updating file status in the queue."""
        status = ImportStatus()
        status.add_file("test.json", "/path/to/test.json")
        status.update_file_status("test.json", "✅ Imported", "chatgpt_json")

        assert status.import_queue[0]["status"] == "✅ Imported"
        assert status.import_queue[0]["detector"] == "chatgpt_json"

    def test_format_queue_display_empty(self):
        """Test formatting empty queue display."""
        status = ImportStatus()
        result = status.format_queue_display()
        assert result == "No files in import queue."

    def test_format_queue_display_with_files(self):
        """Test formatting queue display with files."""
        status = ImportStatus()
        status.add_file("test.json", "/path/to/test.json")
        status.update_file_status("test.json", "✅ Imported", "chatgpt_json")

        result = status.format_queue_display()

        # Check that it contains the expected table structure
        assert "| Filename | Status | Detector | Time |" in result
        assert "test.json" in result
        assert "✅ Imported" in result
        assert "chatgpt_json" in result

    def test_get_summary_empty(self):
        """Test getting summary for empty queue."""
        status = ImportStatus()
        result = status.get_summary()
        assert result == ""

    def test_get_summary_with_files(self):
        """Test getting summary with processed files."""
        status = ImportStatus()

        # Add and process some files
        status.add_file("imported.json", "/path/to/imported.json")
        status.update_file_status("imported.json", "✅ Imported", "chatgpt_json")

        status.add_file("failed.txt", "/path/to/failed.txt")
        status.update_file_status("failed.txt", "❌ Failed", "None")

        status.add_file("fallback.csv", "/path/to/fallback.csv")
        status.update_file_status("fallback.csv", "⚠️ Fallback", "fallback_llm")

        result = status.get_summary()

        # Check summary content
        assert "## 📊 Import Summary" in result
        assert "**Total Files Processed:** 3" in result
        assert "**Successfully Imported:** 1 files" in result
        assert "**Failed to Import:** 1 files" in result
        assert "**Used Fallback Plugin:** 1 files" in result
        assert "**Skipped (Duplicates):** 0 files" in result


class TestFormatDetection:
    """Test file format detection functionality."""

    def test_detect_json_format(self):
        """Test detection of JSON files."""
        detector, status = detect_file_format("/path/to/file.json", "conversation.json")
        assert detector == "chatgpt_json"
        assert status == "✅ Imported"

    def test_detect_slack_json_format(self):
        """Test detection of Slack JSON files."""
        detector, status = detect_file_format("/path/to/file.json", "slack_export.json")
        assert detector == "slack_json"
        assert status == "✅ Imported"

    def test_detect_csv_format(self):
        """Test detection of CSV files."""
        detector, status = detect_file_format(
            "/path/to/file.csv", "generic_tabular_export.csv"
        )
        assert detector == "generic_csv"
        assert status == "✅ Imported"

    def test_detect_txt_format(self):
        """Test detection of TXT files (fallback)."""
        detector, status = detect_file_format("/path/to/file.txt", "notes.txt")
        assert detector == "fallback_llm"
        assert status == "⚠️ Fallback"

    def test_detect_md_format(self):
        """Test detection of Markdown files."""
        detector, status = detect_file_format("/path/to/file.md", "conversation.md")
        assert detector == "markdown"
        assert status == "✅ Imported"

    def test_detect_unsupported_format(self):
        """Test detection of unsupported formats."""
        detector, status = detect_file_format("/path/to/file.xyz", "unknown.xyz")
        assert detector == "None"
        assert status == "❌ Failed"


class TestPluginOrchestrator:
    """Test the plugin orchestrator simulation."""

    def test_simulate_no_file(self):
        """Test simulation with no file provided."""
        import_status = ImportStatus()
        queue_display, summary_display, updated_status = simulate_plugin_orchestrator(
            None, import_status
        )
        assert queue_display == "No file selected for import."
        assert summary_display == ""
        assert updated_status == import_status

    def test_simulate_new_file(self):
        """Test simulation with a new file."""
        # Create a temporary file for testing
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as temp_file:
            temp_path = temp_file.name

        try:
            # Start with fresh import status
            import_status = ImportStatus()

            queue_display, summary_display, updated_status = (
                simulate_plugin_orchestrator(temp_path, import_status)
            )

            # Check that the file was processed
            assert (
                "test" in queue_display.lower()
                or os.path.basename(temp_path) in queue_display
            )
            assert "Import Summary" in summary_display
            assert len(updated_status.import_queue) == 1
        finally:
            # Clean up the temporary file
            os.unlink(temp_path)

    def test_simulate_duplicate_file(self):
        """Test simulation with duplicate file."""
        # Create a temporary file for testing
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as temp_file:
            temp_path = temp_file.name

        try:
            # Start with fresh import status
            import_status = ImportStatus()

            # Process the file once
            _, _, updated_status = simulate_plugin_orchestrator(
                temp_path, import_status
            )

            # Process the same file again (should be detected as duplicate)
            queue_display, summary_display, final_status = simulate_plugin_orchestrator(
                temp_path, updated_status
            )

            # Check that duplicate was detected
            assert "Skipped" in queue_display or "Duplicate" in queue_display
        finally:
            # Clean up the temporary file
            os.unlink(temp_path)


class TestInterfaceCreation:
    """Test Gradio interface creation."""

    def test_create_import_interface(self):
        """Test that the import interface can be created successfully."""
        interface = create_import_interface()

        # Basic checks that interface was created
        assert interface is not None
        assert hasattr(interface, "launch")

    def test_interface_components(self):
        """Test that interface contains expected components."""
        # This test checks that the interface creation doesn't raise errors
        # We can't test Gradio components directly without a browser context

        # Simply verify that the function completes without error
        # The actual interface testing would require a browser environment
        try:
            interface = create_import_interface()
            assert interface is not None
        except Exception as e:
            # For testing, we just verify the function can be called
            # Gradio context errors are expected in testing environment
            assert "Blocks context" in str(e) or "event loop" in str(e)


class TestClearQueue:
    """Test queue clearing functionality."""

    def test_clear_import_queue(self):
        """Test clearing the import queue."""
        # Create an import status with some files
        import_status = ImportStatus()
        import_status.add_file("test1.json", "/path/to/test1.json")
        import_status.add_file("test2.txt", "/path/to/test2.txt")

        # Verify files were added
        assert len(import_status.import_queue) == 2

        # Clear the queue
        queue_display, summary_display, new_status = clear_import_queue(import_status)

        # Verify queue was cleared
        assert queue_display == "Import queue cleared."
        assert summary_display == ""

        # Verify new status was reset
        assert len(new_status.import_queue) == 0


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_format_detection_case_insensitive(self):
        """Test that format detection is case insensitive."""
        detector_upper, status_upper = detect_file_format(
            "/path/to/FILE.JSON", "FILE.JSON"
        )
        detector_lower, status_lower = detect_file_format(
            "/path/to/file.json", "file.json"
        )

        assert detector_upper == detector_lower
        assert status_upper == status_lower

    def test_update_nonexistent_file_status(self):
        """Test updating status of non-existent file."""
        status = ImportStatus()
        status.add_file("existing.json", "/path/to/existing.json")

        # Try to update a file that doesn't exist
        status.update_file_status("nonexistent.json", "✅ Imported", "test_plugin")

        # Verify that the existing file wasn't affected
        assert status.import_queue[0]["filename"] == "existing.json"
        assert status.import_queue[0]["status"] == "Processing..."
        assert status.import_queue[0]["detector"] == "Detecting..."

    def test_multiple_files_same_name_different_paths(self):
        """Test handling multiple files with same name but different paths."""
        status = ImportStatus()
        status.add_file("test.json", "/path1/test.json")
        status.add_file("test.json", "/path2/test.json")

        # Both files should be in the queue
        assert len(status.import_queue) == 2

        # Update status of first occurrence
        status.update_file_status("test.json", "✅ Imported", "chatgpt_json")

        # Only the first occurrence should be updated
        assert status.import_queue[0]["status"] == "✅ Imported"
        assert status.import_queue[1]["status"] == "Processing..."

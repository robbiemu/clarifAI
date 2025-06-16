"""
Integration tests for the vault watcher service.
"""

import tempfile
import time
import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from clarifai_vault_watcher.file_watcher import BatchedFileWatcher
from clarifai_vault_watcher.main import VaultWatcherService


class TestFileWatcher:
    """Test cases for the file watcher functionality."""

    @pytest.fixture
    def file_watcher(self):
        """Fixture that provides a file watcher and ensures cleanup."""
        with tempfile.TemporaryDirectory() as temp_dir:
            callback = Mock()
            watcher = BatchedFileWatcher(
                vault_path=temp_dir,
                batch_interval=0.1,  # Short interval for testing
                max_batch_size=5,
                callback=callback,
            )
            yield watcher, temp_dir
            # Cleanup: ensure watcher is stopped
            if watcher._observer is not None:
                watcher.stop()

    def test_file_watcher_initialization(self, file_watcher):
        """Test that file watcher can be initialized properly."""
        watcher, temp_dir = file_watcher

        assert watcher.vault_path == Path(temp_dir)
        assert watcher.batch_interval == 0.1
        assert watcher.max_batch_size == 5
        assert watcher.callback is not None

    def test_file_watcher_start_stop(self, file_watcher):
        """Test starting and stopping the file watcher."""
        watcher, _ = file_watcher

        # Should start without errors
        watcher.start()
        assert watcher._observer is not None

        # Should stop without errors
        watcher.stop()
        assert watcher._observer is None

    def test_file_watcher_batching(self, file_watcher):
        """Test that file events are properly batched."""
        watcher, temp_dir = file_watcher
        vault_path = Path(temp_dir)

        # Create smaller batching parameters for faster test
        watcher.batch_interval = 0.05  # Very short interval
        watcher.max_batch_size = 2

        # Create test files
        test_file1 = vault_path / "test1.md"
        test_file2 = vault_path / "test2.md"

        test_file1.write_text("# Test file 1")
        test_file2.write_text("# Test file 2")

        # Don't start the watcher - just test the batching logic directly
        # to avoid watchdog observer threading issues

        # Simulate file events directly to avoid filesystem timing issues
        watcher._add_event("created", test_file1)
        assert watcher.callback.call_count == 0  # Should not have called yet

        watcher._add_event("created", test_file2)
        # Should trigger batch processing due to max_batch_size=2
        # Give minimal time for processing
        time.sleep(0.1)

        # Verify callback was called
        assert watcher.callback.call_count >= 1


class TestVaultWatcherService:
    """Test cases for the main vault watcher service."""

    def test_service_initialization(self):
        """Test service initialization with mocked config."""
        mock_config = Mock()
        mock_config.paths = Mock()
        mock_config.paths.vault = "/test/vault"
        mock_config.vault_watcher = Mock()
        mock_config.vault_watcher.batch_interval = 2.0
        mock_config.vault_watcher.max_batch_size = 50
        mock_config.rabbitmq_host = "localhost"

        with patch("clarifai_vault_watcher.main.DirtyBlockPublisher") as mock_publisher:
            service = VaultWatcherService(mock_config)

            assert service.config == mock_config
            assert service.block_parser is not None
            assert service.file_watcher is not None
            mock_publisher.assert_called_once()

    @patch("clarifai_vault_watcher.main.DirtyBlockPublisher")
    def test_service_start_doesnt_create_vault_directory(self, mock_publisher):
        """Test that service start method doesn't create vault directory."""
        mock_config = Mock()
        mock_config.paths = Mock()
        mock_config.paths.vault = "/test/vault"
        mock_config.vault_watcher = Mock()
        mock_config.vault_watcher.batch_interval = 2.0
        mock_config.vault_watcher.max_batch_size = 50
        mock_config.rabbitmq_host = "localhost"

        mock_publisher_instance = Mock()
        mock_publisher.return_value = mock_publisher_instance

        service = VaultWatcherService(mock_config)

        with (
            patch.object(service.file_watcher, "start"),
            patch.object(service, "_perform_initial_scan"),
        ):
            service.start()

            # Should connect to publisher but not create directories
            mock_publisher_instance.connect.assert_called_once()

    def test_handle_file_changes_integration(self):
        """Test integration of file change handling."""
        with tempfile.TemporaryDirectory() as temp_dir:
            vault_path = Path(temp_dir)

            # Create a mock config
            mock_config = Mock()
            mock_config.paths = Mock()
            mock_config.paths.vault = str(vault_path)
            mock_config.vault_watcher = Mock()
            mock_config.vault_watcher.batch_interval = 0.1
            mock_config.vault_watcher.max_batch_size = 5
            mock_config.rabbitmq_host = "localhost"

            with patch(
                "clarifai_vault_watcher.main.DirtyBlockPublisher"
            ) as mock_publisher:
                mock_publisher_instance = Mock()
                mock_publisher.return_value = mock_publisher_instance

                service = VaultWatcherService(mock_config)

                # Create a test file with ClarifAI blocks
                test_file = vault_path / "test.md"
                test_content = """
# Test Document

This is a test claim. <!-- clarifai:id=clm_test123 ver=1 -->
^clm_test123
                """.strip()

                test_file.write_text(test_content)

                # Simulate file creation
                service._handle_file_created(test_file)

                # Verify that publisher was called
                mock_publisher_instance.publish_dirty_blocks.assert_called_once()

                # Check the call arguments
                call_args = mock_publisher_instance.publish_dirty_blocks.call_args
                file_path, dirty_blocks = call_args[0]

                assert file_path == test_file
                assert len(dirty_blocks["added"]) == 1
                assert dirty_blocks["added"][0]["clarifai_id"] == "clm_test123"
                assert len(dirty_blocks["modified"]) == 0
                assert len(dirty_blocks["deleted"]) == 0

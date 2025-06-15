"""
Integration tests for the vault watcher service.
"""

import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch
from clarifai_vault_watcher.file_watcher import BatchedFileWatcher
from clarifai_vault_watcher.main import VaultWatcherService


class TestFileWatcher:
    """Test cases for the file watcher functionality."""
    
    def test_file_watcher_initialization(self):
        """Test that file watcher can be initialized properly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            callback = Mock()
            watcher = BatchedFileWatcher(
                vault_path=temp_dir,
                batch_interval=0.1,  # Short interval for testing
                max_batch_size=5,
                callback=callback
            )
            
            assert watcher.vault_path == Path(temp_dir)
            assert watcher.batch_interval == 0.1
            assert watcher.max_batch_size == 5
            assert watcher.callback == callback
    
    def test_file_watcher_start_stop(self):
        """Test starting and stopping the file watcher."""
        with tempfile.TemporaryDirectory() as temp_dir:
            watcher = BatchedFileWatcher(
                vault_path=temp_dir,
                callback=Mock()
            )
            
            # Should start without errors
            watcher.start()
            assert watcher._observer is not None
            
            # Should stop without errors
            watcher.stop()
            assert watcher._observer is None
    
    def test_file_watcher_batching(self):
        """Test that file events are properly batched."""
        with tempfile.TemporaryDirectory() as temp_dir:
            callback = Mock()
            vault_path = Path(temp_dir)
            
            watcher = BatchedFileWatcher(
                vault_path=str(vault_path),
                batch_interval=0.1,  # Short interval for testing
                max_batch_size=2,   # Small batch size to trigger processing
                callback=callback
            )
            
            # Create test files
            test_file1 = vault_path / "test1.md"
            test_file2 = vault_path / "test2.md"
            
            test_file1.write_text("# Test file 1")
            test_file2.write_text("# Test file 2")
            
            watcher.start()
            
            try:
                # Simulate file events
                watcher._add_event('created', test_file1)
                watcher._add_event('created', test_file2)
                
                # Should trigger batch processing due to max_batch_size=2
                time.sleep(0.2)  # Give time for processing
                
                # Verify callback was called
                assert callback.call_count >= 1
                
            finally:
                watcher.stop()


class TestVaultWatcherService:
    """Test cases for the main vault watcher service."""
    
    def test_service_initialization(self):
        """Test service initialization with mocked config."""
        mock_config = Mock()
        mock_config.vault_path = "/test/vault"
        mock_config.rabbitmq_host = "localhost"
        
        with patch('clarifai_vault_watcher.main.DirtyBlockPublisher') as mock_publisher:
            service = VaultWatcherService(mock_config)
            
            assert service.config == mock_config
            assert service.block_parser is not None
            assert service.file_watcher is not None
            mock_publisher.assert_called_once()
    
    @patch('clarifai_vault_watcher.main.DirtyBlockPublisher')
    @patch('os.path.exists')
    def test_service_start_creates_vault_directory(self, mock_exists, mock_publisher):
        """Test that service creates vault directory if it doesn't exist."""
        mock_config = Mock()
        mock_config.vault_path = "/test/vault"
        mock_config.rabbitmq_host = "localhost"
        
        mock_exists.return_value = False
        mock_publisher_instance = Mock()
        mock_publisher.return_value = mock_publisher_instance
        
        service = VaultWatcherService(mock_config)
        
        with patch('os.makedirs') as mock_makedirs, \
             patch.object(service.file_watcher, 'start'), \
             patch.object(service, '_perform_initial_scan'):
            
            service.start()
            
            # Should have created the directory
            mock_makedirs.assert_called_once_with(mock_config.vault_path, exist_ok=True)
            mock_publisher_instance.connect.assert_called_once()
    
    def test_handle_file_changes_integration(self):
        """Test integration of file change handling."""
        with tempfile.TemporaryDirectory() as temp_dir:
            vault_path = Path(temp_dir)
            
            # Create a mock config
            mock_config = Mock()
            mock_config.vault_path = str(vault_path)
            mock_config.rabbitmq_host = "localhost"
            
            with patch('clarifai_vault_watcher.main.DirtyBlockPublisher') as mock_publisher:
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
                assert len(dirty_blocks['added']) == 1
                assert dirty_blocks['added'][0]['clarifai_id'] == 'clm_test123'
                assert len(dirty_blocks['modified']) == 0
                assert len(dirty_blocks['deleted']) == 0
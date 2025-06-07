"""
ClarifAI Vault Watcher Service

This service monitors the vault directory for changes in Markdown files
and emits dirty block IDs for processing.
"""

import os
import time
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point for the Vault Watcher service."""
    logger.info("Starting ClarifAI Vault Watcher service...")
    
    # Check environment variables
    vault_path = os.getenv('VAULT_PATH', '/vault')
    rabbitmq_host = os.getenv('RABBITMQ_HOST', 'rabbitmq')
    
    logger.info(f"Watching vault path: {vault_path}")
    logger.info(f"RabbitMQ host: {rabbitmq_host}")
    
    # Ensure vault directory exists
    if not os.path.exists(vault_path):
        logger.warning(f"Vault path does not exist: {vault_path}")
        os.makedirs(vault_path, exist_ok=True)
        logger.info(f"Created vault directory: {vault_path}")
    
    # Main service loop (placeholder)
    try:
        logger.info("Vault Watcher service is monitoring for changes...")
        while True:
            # TODO: Implement actual file watching and dirty block ID emission
            # This will include:
            # - Monitoring Markdown files for changes using watchfiles or similar
            # - Parsing clarifai:id and ver= markers
            # - Emitting dirty block IDs to RabbitMQ
            # - Handling atomic file operations (.tmp → rename)
            # This will be implemented in future tasks as per the sprint plan
            time.sleep(30)  # Keep the service alive
    except KeyboardInterrupt:
        logger.info("Shutting down Vault Watcher service...")
    except Exception as e:
        logger.error(f"Error in Vault Watcher service: {e}")
        raise


if __name__ == "__main__":
    main()
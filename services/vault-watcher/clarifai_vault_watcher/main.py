"""
ClarifAI Vault Watcher Service

This service monitors the vault directory for changes in Markdown files
and emits dirty block IDs for processing.
"""

import os
import time
import logging
from clarifai_shared import load_config


def main():
    """Main entry point for the Vault Watcher service."""
    try:
        # Load configuration with validation
        config = load_config(validate=True)

        logger = logging.getLogger(__name__)
        logger.info("Starting ClarifAI Vault Watcher service...")

        # Log configuration details
        logger.info(f"Watching vault path: {config.vault_path}")
        logger.info(f"RabbitMQ host: {config.rabbitmq_host}")

        # Ensure vault directory exists
        if not os.path.exists(config.vault_path):
            logger.warning(f"Vault path does not exist: {config.vault_path}")
            os.makedirs(config.vault_path, exist_ok=True)
            logger.info(f"Created vault directory: {config.vault_path}")

        # Main service loop (placeholder)
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

    except ValueError as e:
        # Configuration validation error
        logging.error(f"Configuration error: {e}")
        logging.error(
            "Please check your .env file and ensure all required variables are set."
        )
        raise
    except KeyboardInterrupt:
        logging.info("Shutting down Vault Watcher service...")
    except Exception as e:
        logging.error(f"Error in Vault Watcher service: {e}")
        raise


if __name__ == "__main__":
    main()

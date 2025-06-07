"""
ClarifAI Core Service - Main Processing Engine

This service handles:
- Claim extraction from text
- Summarization
- Concept linking
- Integration with Neo4j and PostgreSQL
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
    """Main entry point for the ClarifAI Core service."""
    logger.info("Starting ClarifAI Core service...")
    
    # Check environment variables
    vault_path = os.getenv('VAULT_PATH', '/vault')
    rabbitmq_host = os.getenv('RABBITMQ_HOST', 'rabbitmq')
    
    logger.info(f"Vault path: {vault_path}")
    logger.info(f"RabbitMQ host: {rabbitmq_host}")
    
    # Main service loop (placeholder)
    try:
        while True:
            logger.info("ClarifAI Core service is running...")
            time.sleep(30)  # Keep the service alive
    except KeyboardInterrupt:
        logger.info("Shutting down ClarifAI Core service...")
    except Exception as e:
        logger.error(f"Error in ClarifAI Core service: {e}")
        raise


if __name__ == "__main__":
    main()
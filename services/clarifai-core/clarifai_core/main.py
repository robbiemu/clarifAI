"""
ClarifAI Core Service - Main Processing Engine

This service handles:
- Claim extraction from text
- Summarization
- Concept linking
- Integration with Neo4j and PostgreSQL
"""

import time
import logging
from clarifai_shared import load_config


def main():
    """Main entry point for the ClarifAI Core service."""
    try:
        # Load configuration with validation
        config = load_config(validate=True)

        logger = logging.getLogger(__name__)
        logger.info("Starting ClarifAI Core service...")

        # Log configuration details
        logger.info(f"Vault path: {config.vault_path}")
        logger.info(f"RabbitMQ host: {config.rabbitmq_host}")
        logger.info(f"PostgreSQL host: {config.postgres.host}:{config.postgres.port}")
        logger.info(f"Neo4j host: {config.neo4j.host}:{config.neo4j.port}")

        # Test database connections (placeholder for actual connection logic)
        logger.info("Database configuration:")
        logger.info(f"  PostgreSQL URL: {config.postgres.get_connection_url()}")
        logger.info(f"  Neo4j Bolt URL: {config.neo4j.get_neo4j_bolt_url()}")

        # Main service loop (placeholder)
        logger.info("ClarifAI Core service is running...")
        while True:
            # TODO: Implement actual claim extraction, summarization, and concept linking logic
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
        logging.info("Shutting down ClarifAI Core service...")
    except Exception as e:
        logging.error(f"Error in ClarifAI Core service: {e}")
        raise


if __name__ == "__main__":
    main()

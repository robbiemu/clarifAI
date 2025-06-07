"""
ClarifAI Scheduler Service

This service runs periodic jobs including:
- Concept hygiene
- Vault synchronization
- Reprocessing tasks
"""

import os
import time
import logging
from clarifai_shared import load_config


def main():
    """Main entry point for the Scheduler service."""
    try:
        # Load configuration with validation
        config = load_config(validate=True)

        logger = logging.getLogger(__name__)
        logger.info("Starting ClarifAI Scheduler service...")

        # Get automation settings from environment
        automation_pause = os.getenv("AUTOMATION_PAUSE", "false").lower() == "true"
        concept_refresh_enabled = (
            os.getenv("CONCEPT_EMBEDDING_REFRESH_ENABLED", "true").lower() == "true"
        )
        concept_refresh_cron = os.getenv("CONCEPT_EMBEDDING_REFRESH_CRON", "0 3 * * *")

        # Log configuration details
        logger.info(f"Vault path: {config.vault_path}")
        logger.info(f"Automation paused: {automation_pause}")
        logger.info(f"Concept embedding refresh enabled: {concept_refresh_enabled}")
        logger.info(f"Concept embedding refresh cron: {concept_refresh_cron}")

        # Main service loop (placeholder)
        previous_state = None
        current_state = "paused" if automation_pause else "running"
        logger.info(f"Scheduler service is {current_state}...")

        while True:
            # Re-check automation pause state (could be changed via environment)
            automation_pause = os.getenv("AUTOMATION_PAUSE", "false").lower() == "true"
            current_state = "paused" if automation_pause else "running"

            if current_state != previous_state:
                if current_state == "running":
                    logger.info("Scheduler service is running periodic jobs...")
                else:
                    logger.info("Scheduler service is paused...")
                previous_state = current_state

            # TODO: Implement actual periodic jobs (concept hygiene, vault sync, reprocessing)
            # This will be implemented in future tasks as per the sprint plan
            time.sleep(60)  # Check every minute

    except ValueError as e:
        # Configuration validation error
        logging.error(f"Configuration error: {e}")
        logging.error(
            "Please check your .env file and ensure all required variables are set."
        )
        raise
    except KeyboardInterrupt:
        logging.info("Shutting down Scheduler service...")
    except Exception as e:
        logging.error(f"Error in Scheduler service: {e}")
        raise


if __name__ == "__main__":
    main()

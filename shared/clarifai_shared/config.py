"""
Shared configuration system for ClarifAI services.

This module provides environment variable injection from .env files with
fallback logic for external database connections using host.docker.internal.
"""

import os
import logging
from typing import Optional, List
from pathlib import Path
from dataclasses import dataclass, field

try:
    from dotenv import load_dotenv
except ImportError:
    # Fallback if python-dotenv is not available
    def load_dotenv(*args, **kwargs):
        pass


logger = logging.getLogger(__name__)


@dataclass
class DatabaseConfig:
    """Database connection configuration with fallback support."""

    host: str
    port: int
    user: str
    password: str
    database: str = ""

    def get_connection_url(self, scheme: str = "postgresql") -> str:
        """Build database connection URL."""
        if self.database:
            return f"{scheme}://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
        return f"{scheme}://{self.user}:{self.password}@{self.host}:{self.port}"

    def get_neo4j_bolt_url(self) -> str:
        """Get Neo4j bolt connection URL."""
        return f"bolt://{self.host}:{self.port}"


@dataclass
class ClarifAIConfig:
    """Main configuration class for ClarifAI services."""

    # Database configurations
    postgres: DatabaseConfig = field(
        default_factory=lambda: DatabaseConfig("", 0, "", "")
    )
    neo4j: DatabaseConfig = field(default_factory=lambda: DatabaseConfig("", 0, "", ""))

    # Message broker configuration
    rabbitmq_host: str = "rabbitmq"
    rabbitmq_port: int = 5672
    rabbitmq_user: str = "user"
    rabbitmq_password: str = ""

    # Service configuration
    vault_path: str = "/vault"
    settings_path: str = "/settings"
    log_level: str = "INFO"
    debug: bool = False

    # AI/ML configuration
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None

    @classmethod
    def from_env(cls, env_file: Optional[str] = None) -> "ClarifAIConfig":
        """
        Create configuration from environment variables with .env file support.

        Args:
            env_file: Path to .env file (optional, defaults to searching for .env)
        """
        # Load .env file if specified or found
        if env_file:
            load_dotenv(env_file)
        else:
            # Try to find .env file in current directory or parent directories
            current_path = Path.cwd()
            for path in [current_path] + list(current_path.parents):
                env_path = path / ".env"
                if env_path.exists():
                    logger.info(f"Loading environment variables from {env_path}")
                    load_dotenv(env_path)
                    break

        # PostgreSQL configuration with fallback
        postgres_host = os.getenv("POSTGRES_HOST", "postgres")
        postgres_host = cls._apply_host_fallback(postgres_host)

        postgres = DatabaseConfig(
            host=postgres_host,
            port=int(os.getenv("POSTGRES_PORT", "5432")),
            user=os.getenv("POSTGRES_USER", "clarifai"),
            password=os.getenv("POSTGRES_PASSWORD", ""),
            database=os.getenv("POSTGRES_DB", "clarifai"),
        )

        # Neo4j configuration with fallback
        neo4j_host = os.getenv("NEO4J_HOST", "neo4j")
        neo4j_host = cls._apply_host_fallback(neo4j_host)

        neo4j = DatabaseConfig(
            host=neo4j_host,
            port=int(os.getenv("NEO4J_BOLT_PORT", "7687")),
            user=os.getenv("NEO4J_USER", "neo4j"),
            password=os.getenv("NEO4J_PASSWORD", ""),
        )

        return cls(
            postgres=postgres,
            neo4j=neo4j,
            rabbitmq_host=os.getenv("RABBITMQ_HOST", "rabbitmq"),
            rabbitmq_port=int(os.getenv("RABBITMQ_PORT", "5672")),
            rabbitmq_user=os.getenv("RABBITMQ_USER", "user"),
            rabbitmq_password=os.getenv("RABBITMQ_PASSWORD", ""),
            vault_path=os.getenv("VAULT_PATH", "/vault"),
            settings_path=os.getenv("SETTINGS_PATH", "/settings"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            debug=os.getenv("DEBUG", "false").lower() == "true",
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        )

    @staticmethod
    def _apply_host_fallback(host: str) -> str:
        """
        Apply host.docker.internal fallback for external database connections.

        If the host appears to be external (not a Docker service name),
        and we're running in a Docker container, use host.docker.internal.
        """
        # If explicitly set to host.docker.internal, keep it
        if host == "host.docker.internal":
            return host

        # Check if we're running in Docker by looking for typical indicators
        running_in_docker = (
            os.path.exists("/.dockerenv") or os.getenv("DOCKER_CONTAINER") == "true"
        )

        # List of common Docker service names (internal services)
        docker_services = {
            "postgres",
            "neo4j",
            "rabbitmq",
            "clarifai-core",
            "vault-watcher",
            "scheduler",
        }

        # If running in Docker and host is not localhost/127.0.0.1 and not a known service
        if (
            running_in_docker
            and host not in docker_services
            and host not in ("localhost", "127.0.0.1")
        ):
            # Check if it's an IP address or external hostname
            if ClarifAIConfig._is_external_host(host):
                logger.info(
                    f"Applying host.docker.internal fallback for external host: {host}"
                )
                return "host.docker.internal"

        return host

    @staticmethod
    def _is_external_host(host: str) -> bool:
        """Check if a host appears to be external (IP address or FQDN)."""
        import re

        # Check if it's an IP address pattern
        ip_pattern = re.compile(r"^(\d{1,3}\.){3}\d{1,3}$")
        if ip_pattern.match(host):
            return True

        # Check if it contains dots (likely FQDN)
        if "." in host and not host.startswith("localhost"):
            return True

        return False

    def validate_required_vars(
        self, required_vars: Optional[List[str]] = None
    ) -> List[str]:
        """
        Validate that required environment variables are set.

        Args:
            required_vars: List of required variable names (optional)

        Returns:
            List of missing variables
        """
        if required_vars is None:
            required_vars = ["POSTGRES_PASSWORD", "NEO4J_PASSWORD"]

        missing_vars = []

        # Check environment variables directly
        for var in required_vars:
            value = os.getenv(var)
            if not value:
                missing_vars.append(var)

        # Only check config if no direct env vars were specified
        if not required_vars or len(missing_vars) == len(required_vars):
            # Additional validation for database connections via config
            if not self.postgres.password and "POSTGRES_PASSWORD" not in missing_vars:
                missing_vars.append("POSTGRES_PASSWORD (via config)")
            if not self.neo4j.password and "NEO4J_PASSWORD" not in missing_vars:
                missing_vars.append("NEO4J_PASSWORD (via config)")

        return list(set(missing_vars))  # Remove duplicates

    def setup_logging(self):
        """Configure logging based on the log level setting."""
        log_level = getattr(logging, self.log_level.upper(), logging.INFO)
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

        if self.debug:
            logging.getLogger().setLevel(logging.DEBUG)


def load_config(
    env_file: Optional[str] = None,
    validate: bool = True,
    required_vars: Optional[List[str]] = None,
) -> ClarifAIConfig:
    """
    Load ClarifAI configuration with validation.

    Args:
        env_file: Path to .env file (optional)
        validate: Whether to validate required variables
        required_vars: List of required variables to validate

    Returns:
        ClarifAIConfig instance

    Raises:
        ValueError: If required variables are missing
    """
    config = ClarifAIConfig.from_env(env_file)

    if validate:
        missing_vars = config.validate_required_vars(required_vars)
        if missing_vars:
            error_msg = (
                f"Missing required environment variables: {', '.join(missing_vars)}. "
                f"Please check your .env file or environment configuration."
            )
            logger.error(error_msg)
            raise ValueError(error_msg)

    config.setup_logging()
    return config

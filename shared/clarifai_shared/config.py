"""
Shared configuration system for ClarifAI services.

This module provides environment variable injection from .env files with
fallback logic for external database connections using host.docker.internal.
"""

import os
import logging
from typing import Optional, List, Dict, Any
from pathlib import Path
from dataclasses import dataclass, field

try:
    from dotenv import load_dotenv
except ImportError:
    # Fallback if python-dotenv is not available
    def load_dotenv(*args, **kwargs):
        pass


import yaml


logger = logging.getLogger(__name__)


@dataclass
class EmbeddingConfig:
    """Configuration for embedding models and vector storage."""

    # Model settings
    default_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    device: str = "auto"
    batch_size: int = 32

    # PGVector settings
    collection_name: str = "utterances"
    embed_dim: int = 384
    index_type: str = "ivfflat"
    index_lists: int = 100

    # Chunking settings
    chunk_size: int = 300
    chunk_overlap: int = 30
    keep_separator: bool = True
    merge_colon_endings: bool = True
    merge_short_prefixes: bool = True
    min_chunk_tokens: int = 5


@dataclass
class ConceptsConfig:
    """Configuration for concept detection and management."""

    # Concept candidates settings
    candidates_collection: str = "concept_candidates"
    similarity_threshold: float = 0.9

    # Canonical concepts settings
    canonical_collection: str = "concepts"
    merge_threshold: float = 0.95


@dataclass
class PathsConfig:
    """Configuration for vault and file paths."""

    vault: str = "/vault"
    tier1: str = "conversations"
    tier2: str = "summaries"
    tier3: str = "concepts"
    settings: str = "/settings"


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
class VaultPaths:
    """Vault directory structure configuration."""

    vault: str = "/vault"
    settings: str = "/settings"
    tier1: str = "tier1"
    summaries: str = "."
    concepts: str = "."
    logs: str = ".clarifai/import_logs"


@dataclass
class ClarifAIConfig:
    """Main configuration class for ClarifAI services."""

    # Database configurations
    postgres: DatabaseConfig = field(
        default_factory=lambda: DatabaseConfig("", 0, "", "")
    )
    neo4j: DatabaseConfig = field(default_factory=lambda: DatabaseConfig("", 0, "", ""))

    # New configuration sections
    embedding: EmbeddingConfig = field(default_factory=EmbeddingConfig)
    concepts: ConceptsConfig = field(default_factory=ConceptsConfig)

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

    # Vault structure configuration
    paths: VaultPaths = field(default_factory=VaultPaths)

    @classmethod
    def from_env(
        cls, env_file: Optional[str] = None, config_file: Optional[str] = None
    ) -> "ClarifAIConfig":
        """
        Create configuration from environment variables and YAML config file.

        Args:
            env_file: Path to .env file (optional, defaults to searching for .env)
            config_file: Path to YAML config file (optional, defaults to settings/clarifai.config.yaml)
        """
        # Load YAML configuration first
        yaml_config = cls._load_yaml_config(config_file)

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
        postgres_config = yaml_config.get("databases", {}).get("postgres", {})
        postgres_host = os.getenv(
            "POSTGRES_HOST", postgres_config.get("host", "postgres")
        )
        postgres_host = cls._apply_host_fallback(postgres_host)

        postgres = DatabaseConfig(
            host=postgres_host,
            port=int(os.getenv("POSTGRES_PORT", postgres_config.get("port", "5432"))),
            user=os.getenv("POSTGRES_USER", "clarifai"),
            password=os.getenv("POSTGRES_PASSWORD", ""),
            database=os.getenv(
                "POSTGRES_DB", postgres_config.get("database", "clarifai")
            ),
        )

        # Neo4j configuration with fallback
        neo4j_config = yaml_config.get("databases", {}).get("neo4j", {})
        neo4j_host = os.getenv("NEO4J_HOST", neo4j_config.get("host", "neo4j"))
        neo4j_host = cls._apply_host_fallback(neo4j_host)

        neo4j = DatabaseConfig(
            host=neo4j_host,
            port=int(os.getenv("NEO4J_BOLT_PORT", neo4j_config.get("port", "7687"))),
            user=os.getenv("NEO4J_USER", "neo4j"),
            password=os.getenv("NEO4J_PASSWORD", ""),
        )

        # Load embedding configuration from YAML
        embedding_config = yaml_config.get("embedding", {})
        embedding = EmbeddingConfig(
            default_model=embedding_config.get("models", {}).get(
                "default", "sentence-transformers/all-MiniLM-L6-v2"
            ),
            device=embedding_config.get("device", "auto"),
            batch_size=embedding_config.get("batch_size", 32),
            collection_name=embedding_config.get("pgvector", {}).get(
                "collection_name", "utterances"
            ),
            embed_dim=embedding_config.get("pgvector", {}).get("embed_dim", 384),
            index_type=embedding_config.get("pgvector", {}).get(
                "index_type", "ivfflat"
            ),
            index_lists=embedding_config.get("pgvector", {}).get("index_lists", 100),
            chunk_size=embedding_config.get("chunking", {}).get("chunk_size", 300),
            chunk_overlap=embedding_config.get("chunking", {}).get("chunk_overlap", 30),
            keep_separator=embedding_config.get("chunking", {}).get(
                "keep_separator", True
            ),
            merge_colon_endings=embedding_config.get("chunking", {}).get(
                "merge_colon_endings", True
            ),
            merge_short_prefixes=embedding_config.get("chunking", {}).get(
                "merge_short_prefixes", True
            ),
            min_chunk_tokens=embedding_config.get("chunking", {}).get(
                "min_chunk_tokens", 5
            ),
        )

        # Load concepts configuration from YAML
        concepts_config = yaml_config.get("concepts", {})
        concepts = ConceptsConfig(
            candidates_collection=concepts_config.get("candidates", {}).get(
                "collection_name", "concept_candidates"
            ),
            similarity_threshold=concepts_config.get("candidates", {}).get(
                "similarity_threshold", 0.9
            ),
            canonical_collection=concepts_config.get("canonical", {}).get(
                "collection_name", "concepts"
            ),
            merge_threshold=concepts_config.get("canonical", {}).get(
                "similarity_threshold", 0.95
            ),
        )

        # Load paths configuration from YAML
        paths_config = yaml_config.get("paths", {})
        vault_path = os.getenv("VAULT_PATH", paths_config.get("vault", "/vault"))
        settings_path = os.getenv(
            "SETTINGS_PATH", paths_config.get("settings", "/settings")
        )

        # Vault paths configuration (from main branch)
        paths = VaultPaths(
            vault=vault_path,
            settings=settings_path,
            tier1=os.getenv("VAULT_TIER1_PATH", paths_config.get("tier1", "tier1")),
            summaries=os.getenv(
                "VAULT_SUMMARIES_PATH", paths_config.get("summaries", ".")
            ),
            concepts=os.getenv(
                "VAULT_CONCEPTS_PATH", paths_config.get("concepts", ".")
            ),
            logs=os.getenv(
                "VAULT_LOGS_PATH", paths_config.get("logs", ".clarifai/import_logs")
            ),
        )

        return cls(
            postgres=postgres,
            neo4j=neo4j,
            embedding=embedding,
            concepts=concepts,
            rabbitmq_host=os.getenv("RABBITMQ_HOST", "rabbitmq"),
            rabbitmq_port=int(os.getenv("RABBITMQ_PORT", "5672")),
            rabbitmq_user=os.getenv("RABBITMQ_USER", "user"),
            rabbitmq_password=os.getenv("RABBITMQ_PASSWORD", ""),
            vault_path=vault_path,  # For backward compatibility
            settings_path=settings_path,  # For backward compatibility
            log_level=os.getenv(
                "LOG_LEVEL", yaml_config.get("logging", {}).get("level", "INFO")
            ),
            debug=os.getenv("DEBUG", "false").lower() == "true",
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            paths=paths,
        )

    @classmethod
    def _load_yaml_config(cls, config_file: Optional[str] = None) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if yaml is None:
            logger.warning("PyYAML not available, skipping YAML config loading")
            return {}

        if config_file is None:
            # Look for clarifai.config.yaml in settings directory first, then current directory or parent directories
            current_path = Path.cwd()
            search_paths = []

            # Priority 1: settings directory in current and parent directories
            for path in [current_path] + list(current_path.parents):
                search_paths.append(path / "settings" / "clarifai.config.yaml")

            # Priority 2: root level in current and parent directories
            for path in [current_path] + list(current_path.parents):
                search_paths.append(path / "clarifai.config.yaml")

            for config_path in search_paths:
                if config_path.exists():
                    config_file = str(config_path)
                    break

        if config_file and Path(config_file).exists():
            logger.info(f"Loading YAML configuration from {config_file}")
            try:
                with open(config_file, "r") as f:
                    return yaml.safe_load(f) or {}
            except Exception as e:
                logger.error(f"Failed to load YAML config from {config_file}: {e}")
                return {}
        else:
            logger.info("No YAML configuration file found, using defaults")
            return {}

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
    config_file: Optional[str] = None,
    validate: bool = True,
    required_vars: Optional[List[str]] = None,
) -> ClarifAIConfig:
    """
    Load ClarifAI configuration with validation.

    Args:
        env_file: Path to .env file (optional)
        config_file: Path to YAML config file (optional)
        validate: Whether to validate required variables
        required_vars: List of required variables to validate

    Returns:
        ClarifAIConfig instance

    Raises:
        ValueError: If required variables are missing
    """
    config = ClarifAIConfig.from_env(env_file, config_file)

    # Validate required environment variables for security
    if validate:
        # Check other required vars (this will include database passwords)
        missing_vars = config.validate_required_vars(required_vars)

        if missing_vars:
            # Remove duplicates and sort for consistent output
            missing_vars = sorted(list(set(missing_vars)))
            error_msg = (
                f"Missing required environment variables: {', '.join(missing_vars)}. "
                f"Please check your .env file or environment configuration."
            )
            logger.error(error_msg)
            raise ValueError(error_msg)

    config.setup_logging()
    return config

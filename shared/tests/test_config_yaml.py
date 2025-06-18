"""
Tests for aclarai configuration with YAML support.

These tests verify the configuration loading and YAML integration.
"""

import pytest
import os
from unittest.mock import patch, mock_open

from aclarai_shared.config import (
    aclaraiConfig,
    EmbeddingConfig,
    ConceptsConfig,
    PathsConfig,
    load_config,
)


def test_embedding_config_defaults():
    """Test EmbeddingConfig default values."""
    config = EmbeddingConfig()

    assert config.default_model == "sentence-transformers/all-MiniLM-L6-v2"
    assert config.device == "auto"
    assert config.batch_size == 32
    assert config.collection_name == "utterances"
    assert config.embed_dim == 384
    assert config.chunk_size == 300
    assert config.chunk_overlap == 30
    assert config.merge_colon_endings is True
    assert config.merge_short_prefixes is True
    assert config.min_chunk_tokens == 5


def test_concepts_config_defaults():
    """Test ConceptsConfig default values."""
    config = ConceptsConfig()

    assert config.candidates_collection == "concept_candidates"
    assert config.similarity_threshold == 0.9
    assert config.canonical_collection == "concepts"
    assert config.merge_threshold == 0.95


def test_paths_config_defaults():
    """Test PathsConfig default values."""
    config = PathsConfig()

    assert config.vault == "/vault"
    assert config.tier1 == "conversations"
    assert config.tier2 == "summaries"
    assert config.tier3 == "concepts"
    assert config.settings == "/settings"


def test_aclarai_config_with_yaml():
    """Test aclarai config loading with YAML content."""
    yaml_content = """
databases:
  postgres:
    host: "test-postgres"
    port: 5433
    database: "test_db"
  neo4j:
    host: "test-neo4j"
    port: 7688

embedding:
  models:
    default: "custom/embedding-model"
  device: "cuda"
  batch_size: 64
  pgvector:
    collection_name: "test_utterances"
    embed_dim: 512
  chunking:
    chunk_size: 500
    chunk_overlap: 50

concepts:
  candidates:
    collection_name: "test_candidates"
    similarity_threshold: 0.85

paths:
  vault: "/test/vault"
  tier1: "test_conversations"
"""

    # Mock file operations
    with (
        patch("builtins.open", mock_open(read_data=yaml_content)),
        patch("pathlib.Path.exists", return_value=True),
        patch("aclarai_shared.config.yaml.safe_load") as mock_yaml_load,
    ):
        # Setup yaml mock to return parsed content
        mock_yaml_load.return_value = {
            "databases": {
                "postgres": {
                    "host": "test-postgres",
                    "port": 5433,
                    "database": "test_db",
                },
                "neo4j": {"host": "test-neo4j", "port": 7688},
            },
            "embedding": {
                "models": {"default": "custom/embedding-model"},
                "device": "cuda",
                "batch_size": 64,
                "pgvector": {"collection_name": "test_utterances", "embed_dim": 512},
                "chunking": {"chunk_size": 500, "chunk_overlap": 50},
            },
            "concepts": {
                "candidates": {
                    "collection_name": "test_candidates",
                    "similarity_threshold": 0.85,
                }
            },
            "paths": {"vault": "/test/vault", "tier1": "test_conversations"},
        }

        # Set environment variables to avoid loading real .env
        with patch.dict(
            os.environ,
            {
                "POSTGRES_USER": "test_user",
                "POSTGRES_PASSWORD": "test_pass",
                "NEO4J_USER": "neo4j_user",
                "NEO4J_PASSWORD": "neo4j_pass",
            },
        ):
            config = aclaraiConfig.from_env(config_file="test.yaml")

            # Verify database config uses YAML values
            assert config.postgres.host == "test-postgres"
            assert config.postgres.port == 5433
            assert config.postgres.database == "test_db"
            assert config.neo4j.host == "test-neo4j"
            assert config.neo4j.port == 7688

            # Verify embedding config uses YAML values
            assert config.embedding.default_model == "custom/embedding-model"
            assert config.embedding.device == "cuda"
            assert config.embedding.batch_size == 64
            assert config.embedding.collection_name == "test_utterances"
            assert config.embedding.embed_dim == 512
            assert config.embedding.chunk_size == 500
            assert config.embedding.chunk_overlap == 50

            # Verify concepts config
            assert config.concepts.candidates_collection == "test_candidates"
            assert config.concepts.similarity_threshold == 0.85

            # Verify paths config
            assert config.paths.vault == "/test/vault"
            assert config.paths.tier1 == "test_conversations"


def test_config_environment_override():
    """Test that environment variables override YAML values."""
    yaml_content = """
databases:
  postgres:
    host: "yaml-postgres"
    port: 5432
"""

    with (
        patch("builtins.open", mock_open(read_data=yaml_content)),
        patch("pathlib.Path.exists", return_value=True),
        patch("aclarai_shared.config.yaml.safe_load") as mock_yaml_load,
    ):
        mock_yaml_load.return_value = {
            "databases": {"postgres": {"host": "yaml-postgres", "port": 5432}}
        }

        # Environment variables should override YAML
        with patch.dict(
            os.environ,
            {
                "POSTGRES_HOST": "env-postgres",
                "POSTGRES_PORT": "5433",
                "POSTGRES_USER": "env_user",
                "POSTGRES_PASSWORD": "env_pass",
                "NEO4J_USER": "neo4j",
                "NEO4J_PASSWORD": "neo4j_pass",
            },
        ):
            config = aclaraiConfig.from_env(config_file="test.yaml")

            # Environment values should win
            assert config.postgres.host == "env-postgres"
            assert config.postgres.port == 5433
            assert config.postgres.user == "env_user"
            assert config.postgres.password == "env_pass"


def test_config_without_yaml():
    """Test config loading when no YAML file exists."""
    with (
        patch("pathlib.Path.exists", return_value=False),
        patch.dict(
            os.environ,
            {
                "POSTGRES_USER": "test_user",
                "POSTGRES_PASSWORD": "test_pass",
                "NEO4J_USER": "neo4j",
                "NEO4J_PASSWORD": "neo4j_pass",
            },
        ),
    ):
        config = aclaraiConfig.from_env()

        # Should use defaults when no YAML
        assert config.postgres.host == "postgres"  # Default
        assert (
            config.embedding.default_model == "sentence-transformers/all-MiniLM-L6-v2"
        )
        assert config.embedding.chunk_size == 300
        assert config.paths.vault == "/vault"


def test_load_config_function():
    """Test the load_config convenience function."""
    with (
        patch("aclarai_shared.config.aclaraiConfig.from_env") as mock_from_env,
        patch.dict(
            os.environ,
            {"POSTGRES_PASSWORD": "test_pass", "NEO4J_PASSWORD": "neo4j_pass"},
        ),
    ):
        mock_config = aclaraiConfig()
        mock_from_env.return_value = mock_config

        # Test with validation disabled
        config = load_config(validate=False)
        assert config == mock_config
        mock_from_env.assert_called_once_with(None, None)


def test_load_config_validation_failure():
    """Test config validation failure."""
    with patch("aclarai_shared.config.aclaraiConfig.from_env") as mock_from_env:
        mock_config = aclaraiConfig()
        mock_from_env.return_value = mock_config

        # Missing required environment variables
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError) as exc_info:
                load_config(validate=True)

            assert "Missing required environment variables" in str(exc_info.value)


def test_yaml_loading_error_handling():
    """Test graceful handling of YAML loading errors."""
    with (
        patch("builtins.open", mock_open(read_data="invalid: yaml: content:")),
        patch("pathlib.Path.exists", return_value=True),
        patch(
            "aclarai_shared.config.yaml.safe_load", side_effect=Exception("YAML error")
        ),
    ):
        with patch.dict(
            os.environ,
            {
                "POSTGRES_USER": "test_user",
                "POSTGRES_PASSWORD": "test_pass",
                "NEO4J_USER": "neo4j",
                "NEO4J_PASSWORD": "neo4j_pass",
            },
        ):
            # Should not raise exception, should use defaults
            config = aclaraiConfig.from_env(config_file="invalid.yaml")

            # Should fall back to defaults
            assert config.postgres.host == "postgres"
            assert (
                config.embedding.default_model
                == "sentence-transformers/all-MiniLM-L6-v2"
            )


def test_yaml_module_not_available():
    """Test behavior when PyYAML is not available."""
    with patch("aclarai_shared.config.yaml", None):
        with patch.dict(
            os.environ,
            {
                "POSTGRES_USER": "test_user",
                "POSTGRES_PASSWORD": "test_pass",
                "NEO4J_USER": "neo4j",
                "NEO4J_PASSWORD": "neo4j_pass",
            },
        ):
            config = aclaraiConfig.from_env(config_file="test.yaml")

            # Should use defaults when YAML not available
            assert config.postgres.host == "postgres"
            assert (
                config.embedding.default_model
                == "sentence-transformers/all-MiniLM-L6-v2"
            )


def test_config_backward_compatibility():
    """Test that deprecated fields still work for backward compatibility."""
    with (
        patch("pathlib.Path.exists", return_value=False),
        patch.dict(
            os.environ,
            {
                "VAULT_PATH": "/custom/vault",
                "SETTINGS_PATH": "/custom/settings",
                "POSTGRES_USER": "test_user",
                "POSTGRES_PASSWORD": "test_pass",
                "NEO4J_USER": "neo4j",
                "NEO4J_PASSWORD": "neo4j_pass",
            },
        ),
    ):
        config = aclaraiConfig.from_env()

        # New paths config should be updated
        assert config.paths.vault == "/custom/vault"
        assert config.paths.settings == "/custom/settings"

        # Deprecated fields should match for backward compatibility
        assert config.vault_path == "/custom/vault"
        assert config.settings_path == "/custom/settings"

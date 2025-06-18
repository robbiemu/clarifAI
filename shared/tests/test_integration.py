"""
Integration test for environment variable injection system.

This test creates a temporary .env file and verifies that services
can load configuration correctly with various scenarios.
"""

import os
import tempfile
import pytest
from pathlib import Path
from aclarai_shared import load_config


class TestEnvironmentIntegration:
    """Integration tests for the environment variable system."""

    def test_dotenv_file_integration(self):
        """Test complete .env file integration."""
        # Save and clear environment variables that might interfere
        env_vars_to_clear = [
            "POSTGRES_HOST",
            "POSTGRES_PORT",
            "POSTGRES_USER",
            "POSTGRES_PASSWORD",
            "POSTGRES_DB",
            "NEO4J_HOST",
            "NEO4J_BOLT_PORT",
            "NEO4J_USER",
            "NEO4J_PASSWORD",
            "RABBITMQ_HOST",
            "RABBITMQ_PORT",
            "VAULT_PATH",
            "LOG_LEVEL",
            "DEBUG",
            "OPENAI_API_KEY",
            "ANTHROPIC_API_KEY",
            "DOCKER_CONTAINER",
        ]
        original_env = {}
        for var in env_vars_to_clear:
            if var in os.environ:
                original_env[var] = os.environ[var]
                del os.environ[var]

        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                # Create a test .env file
                env_file = Path(temp_dir) / ".env"
                env_content = """
# Test environment configuration
POSTGRES_HOST=external-postgres.example.com
POSTGRES_PORT=5432
POSTGRES_USER=test_user
POSTGRES_PASSWORD=fake_test_password_123
POSTGRES_DB=test_db

NEO4J_HOST=external-neo4j.example.com
NEO4J_BOLT_PORT=7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=fake_neo4j_test_password_456

RABBITMQ_HOST=external-rabbitmq.example.com
RABBITMQ_PORT=5672

VAULT_PATH=/custom/vault
LOG_LEVEL=DEBUG
DEBUG=true

OPENAI_API_KEY=sk-fake_test_key_1234567890abcdef
ANTHROPIC_API_KEY=sk-ant-fake_test_key_9876543210fedcba
"""
                env_file.write_text(env_content)

                # Load configuration from the test file
                config = load_config(env_file=str(env_file), validate=True)

                # Note: hosts might be converted to host.docker.internal if Docker environment is detected
                # but the original configuration loading from .env should work
                assert config.postgres.port == 5432
                assert config.postgres.user == "test_user"
                assert config.postgres.password == "fake_test_password_123"
                assert config.postgres.database == "test_db"

                assert config.neo4j.port == 7687
                assert config.neo4j.user == "neo4j"
                assert config.neo4j.password == "fake_neo4j_test_password_456"

                # Verify connection URLs can be generated (host might be fallback)
                postgres_url = config.postgres.get_connection_url()
                assert "test_user:fake_test_password_123" in postgres_url
                assert ":5432/test_db" in postgres_url

                neo4j_url = config.neo4j.get_neo4j_bolt_url()
                assert ":7687" in neo4j_url

                # Verify other settings that shouldn't be affected by fallback
                assert config.vault_path == "/custom/vault"
                assert config.log_level == "DEBUG"
                assert config.debug is True
                assert config.openai_api_key == "sk-fake_test_key_1234567890abcdef"
                assert (
                    config.anthropic_api_key == "sk-ant-fake_test_key_9876543210fedcba"
                )

        finally:
            # Restore original environment
            for var, value in original_env.items():
                os.environ[var] = value

    def test_host_docker_internal_fallback_integration(self):
        """Test the complete host.docker.internal fallback scenario."""
        # Set up environment to simulate Docker container
        original_env = {}
        test_vars = {
            "DOCKER_CONTAINER": "true",
            "POSTGRES_HOST": "192.168.1.100",
            "POSTGRES_PASSWORD": "fake_test_db_password_123",
            "NEO4J_HOST": "my-external-neo4j.local",
            "NEO4J_PASSWORD": "fake_test_neo4j_password_456",
        }

        # Save original values and set test values
        for var, value in test_vars.items():
            if var in os.environ:
                original_env[var] = os.environ[var]
            os.environ[var] = value

        try:
            config = load_config(validate=True)

            # Both hosts should be converted to host.docker.internal
            assert config.postgres.host == "host.docker.internal"
            assert config.neo4j.host == "host.docker.internal"

            # Connection URLs should use the fallback
            postgres_url = config.postgres.get_connection_url()
            assert "host.docker.internal" in postgres_url

            neo4j_url = config.neo4j.get_neo4j_bolt_url()
            assert neo4j_url == "bolt://host.docker.internal:7687"

        finally:
            # Restore original environment
            for var in test_vars:
                if var in original_env:
                    os.environ[var] = original_env[var]
                else:
                    del os.environ[var]

    def test_validation_with_missing_passwords(self):
        """Test validation behavior with missing critical variables."""
        # Clear password variables
        original_postgres = os.environ.get("POSTGRES_PASSWORD")
        original_neo4j = os.environ.get("NEO4J_PASSWORD")

        if "POSTGRES_PASSWORD" in os.environ:
            del os.environ["POSTGRES_PASSWORD"]
        if "NEO4J_PASSWORD" in os.environ:
            del os.environ["NEO4J_PASSWORD"]

        try:
            with pytest.raises(ValueError) as exc_info:
                load_config(validate=True)

            error_msg = str(exc_info.value)
            assert "Missing required environment variables" in error_msg
            assert "POSTGRES_PASSWORD" in error_msg
            assert "NEO4J_PASSWORD" in error_msg

        finally:
            # Restore original values
            if original_postgres:
                os.environ["POSTGRES_PASSWORD"] = original_postgres
            if original_neo4j:
                os.environ["NEO4J_PASSWORD"] = original_neo4j

    def test_service_config_patterns(self):
        """Test patterns that services would use."""
        # Test without validation (for UI service)
        ui_config = load_config(validate=False)
        assert ui_config is not None
        assert hasattr(ui_config, "postgres")
        assert hasattr(ui_config, "neo4j")

        # Test with minimal required environment for core services
        os.environ["POSTGRES_PASSWORD"] = "fake_test_core_password_789"
        os.environ["NEO4J_PASSWORD"] = "fake_test_core_neo4j_password_012"

        try:
            core_config = load_config(validate=True)
            assert core_config is not None

            # Test logging setup
            core_config.setup_logging()

            # Test validation passes
            missing = core_config.validate_required_vars()
            assert len(missing) == 0

        finally:
            # Clean up
            if "POSTGRES_PASSWORD" in os.environ:
                del os.environ["POSTGRES_PASSWORD"]
            if "NEO4J_PASSWORD" in os.environ:
                del os.environ["NEO4J_PASSWORD"]

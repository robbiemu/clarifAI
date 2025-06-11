"""
Pytest configuration and fixtures for ClarifAI tests.
"""

import pytest


def pytest_addoption(parser):
    """Add custom command line options for pytest."""
    parser.addoption(
        "--integration",
        action="store_true",
        default=False,
        help="Run integration tests against real services (requires running PostgreSQL and Neo4j)",
    )


@pytest.fixture
def integration_mode(request):
    """Fixture to determine if tests should run in integration mode."""
    return request.config.getoption("--integration")

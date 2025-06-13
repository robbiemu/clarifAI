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


def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test requiring real services"
    )


def pytest_collection_modifyitems(config, items):
    """Skip integration tests unless --integration is specified."""
    if config.getoption("--integration"):
        # Integration mode - run all tests
        return

    # Unit test mode - skip integration tests
    skip_integration = pytest.mark.skip(
        reason="integration tests require --integration flag"
    )
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip_integration)

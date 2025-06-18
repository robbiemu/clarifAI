"""
Pytest configuration and fixtures for aclarai tests.
"""

import pytest


def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test requiring real services"
    )


def pytest_collection_modifyitems(config, items):
    """Skip integration tests unless -m integration is specified."""
    if config.getoption("-m") == "integration":
        # Integration mode - run only integration tests
        return

    # Unit test mode - skip integration tests by default
    skip_integration = pytest.mark.skip(
        reason="integration tests require -m integration flag"
    )
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip_integration)

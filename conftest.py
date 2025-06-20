"""Pytest configuration for aclarai-ui tests."""

import os
import sys

import pytest

# Add the aclarai_ui module to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
try:
    from playwright.sync_api import sync_playwright

    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
# Only configure Playwright fixtures if it's available
if PLAYWRIGHT_AVAILABLE:

    @pytest.fixture(scope="session")
    def browser():
        """Provide a browser instance for testing."""
        with sync_playwright() as p:
            # Use chromium with minimal setup
            browser = p.chromium.launch(headless=True)
            yield browser
            browser.close()

    @pytest.fixture
    def page(browser):
        """Provide a page instance for testing."""
        if browser is None:
            pytest.skip("Browser not available")
        context = browser.new_context()
        page = context.new_page()
        yield page
        context.close()
else:

    @pytest.fixture
    def browser():
        """Dummy browser fixture when Playwright is not available."""
        pytest.skip("Playwright not available")

    @pytest.fixture
    def page():
        """Dummy page fixture when Playwright is not available."""
        pytest.skip("Playwright not available")

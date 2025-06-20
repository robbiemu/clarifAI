"""Integration tests for the configuration panel UI functionality."""

import os
import sys
import tempfile
from pathlib import Path

import pytest
import yaml
from playwright.sync_api import Page, expect

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from aclarai_ui.config_panel import create_configuration_panel


class TestConfigurationPanelIntegration:
    """Integration tests for configuration panel UI using Playwright."""

    @pytest.fixture(scope="class")
    def gradio_app(self):
        """Create and launch Gradio app for testing."""
        # Create configuration panel interface
        interface = create_configuration_panel()
        # Launch with a free port
        interface.launch(
            server_name="127.0.0.1",
            server_port=0,  # Let Gradio choose a free port
            share=False,
            debug=False,
            quiet=True,
            prevent_thread_lock=True,
        )
        # Get the actual port and URL
        url = interface.local_url
        yield url
        # Cleanup: close the interface
        interface.close()

    @pytest.fixture
    def temp_config_files(self):
        """Create temporary configuration files for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "aclarai.config.yaml"
            default_path = Path(temp_dir) / "aclarai.config.default.yaml"
            # Create default configuration
            default_config = {
                "model": {
                    "claimify": {"default": "gpt-3.5-turbo"},
                    "concept_linker": "gpt-3.5-turbo",
                    "concept_summary": "gpt-4",
                    "subject_summary": "claude-3-sonnet",
                    "trending_concepts_agent": "gpt-3.5-turbo",
                    "fallback_plugin": "gpt-3.5-turbo",
                },
                "embedding": {
                    "utterance": "text-embedding-3-small",
                    "concept": "sentence-transformers/all-MiniLM-L6-v2",
                    "summary": "text-embedding-3-small",
                    "fallback": "text-embedding-3-small",
                },
                "threshold": {
                    "concept_merge": 0.90,
                    "claim_link_strength": 0.60,
                },
                "window": {
                    "claimify": {
                        "p": 3,
                        "f": 1,
                    }
                },
            }
            with open(default_path, "w") as f:
                yaml.safe_dump(default_config, f)
            yield config_path, default_path, default_config

    @pytest.mark.integration
    def test_configuration_panel_loads(self, page: Page, gradio_app):
        """Test that the configuration panel loads correctly."""
        page.goto(gradio_app)
        # Wait for the page to load
        page.wait_for_selector("h1", timeout=10000)
        # Check that the main heading is present
        expect(page.locator("h1")).to_contain_text("Configuration Panel")
        # Check that key sections are present
        expect(page.locator("text=Model & Embedding Settings")).to_be_visible()
        expect(page.locator("text=Thresholds & Parameters")).to_be_visible()

    @pytest.mark.integration
    def test_model_input_validation(self, page: Page, gradio_app):
        """Test that model input validation works in the UI."""
        page.goto(gradio_app)
        page.wait_for_selector("h1", timeout=10000)
        # Find the claimify default model input
        claimify_default_input = page.locator(
            'input[placeholder*="gpt-3.5-turbo"]'
        ).first
        # Enter an invalid model name
        claimify_default_input.fill("invalid-model-name")
        # Find and click the save button
        save_button = page.locator('button:has-text("Save Changes")')
        save_button.click()
        # Wait for validation response
        page.wait_for_timeout(1000)
        # Check that validation error appears
        expect(page.locator("text=Validation Errors")).to_be_visible()
        expect(page.locator("text=Claimify Default")).to_be_visible()

    @pytest.mark.integration
    def test_threshold_input_validation(self, page: Page, gradio_app):
        """Test that threshold input validation works in the UI."""
        page.goto(gradio_app)
        page.wait_for_selector("h1", timeout=10000)
        # Find the concept merge threshold input
        threshold_input = page.locator('input[type="number"]').first
        # Enter an invalid threshold value (> 1.0)
        threshold_input.fill("1.5")
        # Find and click the save button
        save_button = page.locator('button:has-text("Save Changes")')
        save_button.click()
        # Wait for validation response
        page.wait_for_timeout(1000)
        # Check that validation error appears
        expect(page.locator("text=Validation Errors")).to_be_visible()

    @pytest.mark.integration
    def test_window_parameter_validation(self, page: Page, gradio_app):
        """Test that window parameter validation works in the UI."""
        page.goto(gradio_app)
        page.wait_for_selector("h1", timeout=10000)
        # Find the window parameter inputs and enter an invalid window value (> 10)
        # Find the "Previous Sentences" input specifically
        page.locator("text=Previous Sentences").locator("..//input").fill("15")
        # Find and click the save button
        save_button = page.locator('button:has-text("Save Changes")')
        save_button.click()
        # Wait for validation response
        page.wait_for_timeout(1000)
        # Check that validation error appears
        expect(page.locator("text=Validation Errors")).to_be_visible()

    @pytest.mark.integration
    def test_successful_configuration_save(self, page: Page, gradio_app):
        """Test that valid configuration can be saved successfully."""
        page.goto(gradio_app)
        page.wait_for_selector("h1", timeout=10000)
        # Fill in valid configuration values
        claimify_default_input = page.locator(
            'input[placeholder*="gpt-3.5-turbo"]'
        ).first
        claimify_default_input.fill("gpt-4")
        # Find concept linker input and update it
        concept_linker_input = page.locator("text=Concept Linker").locator("..//input")
        concept_linker_input.fill("claude-3-opus")
        # Find and click the save button
        save_button = page.locator('button:has-text("Save Changes")')
        save_button.click()
        # Wait for save response
        page.wait_for_timeout(2000)
        # Check that success message appears
        expect(page.locator("text=Configuration saved successfully")).to_be_visible()

    @pytest.mark.integration
    def test_reload_configuration(self, page: Page, gradio_app):
        """Test that configuration can be reloaded from file."""
        page.goto(gradio_app)
        page.wait_for_selector("h1", timeout=10000)
        # Change a value
        claimify_default_input = page.locator(
            'input[placeholder*="gpt-3.5-turbo"]'
        ).first
        claimify_default_input.fill("changed-value")
        # Find and click the reload button
        reload_button = page.locator('button:has-text("Reload from File")')
        reload_button.click()
        # Wait for reload response
        page.wait_for_timeout(2000)
        # Check that value is restored
        # Note: This depends on having a valid config file, so may restore to default
        current_value = claimify_default_input.input_value()
        # The value should either be the original or a default from file
        assert current_value != "changed-value"
        # Check that reload message appears
        expect(page.locator("text=Configuration reloaded")).to_be_visible()

    @pytest.mark.integration
    def test_all_input_fields_present(self, page: Page, gradio_app):
        """Test that all expected input fields are present in the UI."""
        page.goto(gradio_app)
        page.wait_for_selector("h1", timeout=10000)
        # Check that all expected input labels are present
        expected_labels = [
            "Default Model",
            "Selection Model",
            "Disambiguation Model",
            "Decomposition Model",
            "Concept Linker",
            "Concept Summary",
            "Subject Summary",
            "Trending Concepts Agent",
            "Fallback Plugin",
            "Utterance Embeddings",
            "Concept Embeddings",
            "Summary Embeddings",
            "Fallback Embeddings",
            "Concept Merge Threshold",
            "Claim Link Strength",
            "Previous Sentences",
            "Following Sentences",
        ]
        for label in expected_labels:
            expect(page.locator(f"text={label}")).to_be_visible()

    @pytest.mark.integration
    def test_buttons_present_and_functional(self, page: Page, gradio_app):
        """Test that save and reload buttons are present and clickable."""
        page.goto(gradio_app)
        page.wait_for_selector("h1", timeout=10000)
        # Check that buttons are present
        save_button = page.locator('button:has-text("Save Changes")')
        reload_button = page.locator('button:has-text("Reload from File")')
        expect(save_button).to_be_visible()
        expect(reload_button).to_be_visible()
        # Test that buttons are clickable
        expect(save_button).to_be_enabled()
        expect(reload_button).to_be_enabled()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])

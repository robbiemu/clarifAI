"""
Prompt template loader utility for externalized YAML templates.

Implements the LLM interaction strategy for loading prompt templates
from external YAML files at runtime, as defined in docs/arch/on-llm_interaction_strategy.md
"""

import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class PromptTemplate:
    """Container for a loaded prompt template with metadata."""

    role: str
    description: str
    template: str
    variables: Dict[str, Any]
    system_prompt: Optional[str] = None
    instructions: Optional[list] = None
    output_format: Optional[str] = None
    rules: Optional[list] = None


class PromptLoader:
    """Utility class for loading externalized prompt templates from YAML files."""

    def __init__(
        self,
        prompts_dir: Optional[Path] = None,
        user_prompts_dir: Optional[Path] = None,
    ):
        """
        Initialize the prompt loader.

        Args:
            prompts_dir: Directory containing built-in prompt YAML files.
                        Defaults to shared/clarifai_shared/prompts/
            user_prompts_dir: Directory containing user-customized prompt files.
                             Defaults to ./prompts/ relative to current working directory
        """
        if prompts_dir is None:
            # Default to the prompts directory in clarifai_shared
            current_file = Path(__file__)
            self.prompts_dir = current_file.parent.parent / "prompts"
        else:
            self.prompts_dir = Path(prompts_dir)

        if user_prompts_dir is None:
            # Default to prompts directory in settings (accessible to users in Docker)
            # Fallback to project root for local development
            try:
                # Try relative import first (when imported as part of package)
                from ..config import load_config

                config = load_config(validate=False)
                settings_prompts_dir = Path(config.settings_path) / "prompts"
                # Use settings/prompts if vault path exists, otherwise fallback to ./prompts
                if Path(config.settings_path).exists():
                    self.user_prompts_dir = settings_prompts_dir
                else:
                    self.user_prompts_dir = Path.cwd() / "prompts"
            except (ImportError, ValueError):
                # Try absolute import (when imported directly)
                try:
                    import importlib.util

                    # Find the config module
                    current_file = Path(__file__)
                    config_path = current_file.parent.parent / "config.py"
                    if config_path.exists():
                        spec = importlib.util.spec_from_file_location(
                            "config", config_path
                        )
                        config_module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(config_module)

                        config = config_module.load_config(validate=False)
                        settings_prompts_dir = Path(config.settings_path) / "prompts"
                        # Use settings/prompts if vault path exists, otherwise fallback to ./prompts
                        if Path(config.settings_path).exists():
                            self.user_prompts_dir = settings_prompts_dir
                        else:
                            self.user_prompts_dir = Path.cwd() / "prompts"
                    else:
                        raise ImportError("Config module not found")
                except Exception:
                    # Fallback to original behavior if config loading fails
                    self.user_prompts_dir = Path.cwd() / "prompts"
        else:
            self.user_prompts_dir = Path(user_prompts_dir)

        if not self.prompts_dir.exists():
            logger.warning(
                f"Built-in prompts directory does not exist: {self.prompts_dir}"
            )

        # User prompts directory is optional
        if self.user_prompts_dir.exists():
            logger.debug(f"User prompts directory found: {self.user_prompts_dir}")

    def _find_template_file(self, template_name: str) -> Path:
        """
        Find the template file, checking user directory first, then built-in directory.

        Args:
            template_name: Name of the template file (without .yaml extension)

        Returns:
            Path to the template file

        Raises:
            FileNotFoundError: If template file doesn't exist in either location
        """
        # Check user prompts directory first
        user_template_path = self.user_prompts_dir / f"{template_name}.yaml"
        if user_template_path.exists():
            logger.debug(f"Using user-customized prompt: {user_template_path}")
            return user_template_path

        # Fall back to built-in prompts directory
        builtin_template_path = self.prompts_dir / f"{template_name}.yaml"
        if builtin_template_path.exists():
            logger.debug(f"Using built-in prompt: {builtin_template_path}")
            return builtin_template_path

        # Neither location has the template
        raise FileNotFoundError(
            f"Prompt template '{template_name}' not found in user prompts ({user_template_path}) "
            f"or built-in prompts ({builtin_template_path})"
        )

    def load_template(self, template_name: str) -> PromptTemplate:
        """
        Load a prompt template from a YAML file.

        Checks user-customized prompts directory first, then falls back to built-in prompts.

        Args:
            template_name: Name of the template file (without .yaml extension)

        Returns:
            PromptTemplate instance with loaded data

        Raises:
            FileNotFoundError: If template file doesn't exist
            ValueError: If template is malformed or missing required fields
        """
        template_path = self._find_template_file(template_name)

        try:
            with open(template_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in template {template_name}: {e}")

        # Validate required fields
        required_fields = ["role", "description", "template", "variables"]
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise ValueError(
                f"Template {template_name} missing required fields: {missing_fields}"
            )

        logger.debug(f"Loaded prompt template: {template_name} from {template_path}")

        return PromptTemplate(
            role=data["role"],
            description=data["description"],
            template=data["template"],
            variables=data["variables"],
            system_prompt=data.get("system_prompt"),
            instructions=data.get("instructions"),
            output_format=data.get("output_format"),
            rules=data.get("rules"),
        )

    def format_template(self, template: PromptTemplate, **kwargs) -> str:
        """
        Format a template with provided variables.

        Args:
            template: The loaded template
            **kwargs: Variable values to inject into the template

        Returns:
            Formatted prompt string

        Raises:
            ValueError: If required variables are missing
        """
        # Check for required variables
        required_vars = [
            var_name
            for var_name, var_config in template.variables.items()
            if var_config.get("required", False)
        ]

        missing_vars = [var for var in required_vars if var not in kwargs]
        if missing_vars:
            raise ValueError(f"Missing required template variables: {missing_vars}")

        try:
            return template.template.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"Template formatting error - missing variable: {e}")

    def load_and_format(self, template_name: str, **kwargs) -> str:
        """
        Convenience method to load a template and format it in one call.

        Args:
            template_name: Name of the template file (without .yaml extension)
            **kwargs: Variable values to inject into the template

        Returns:
            Formatted prompt string
        """
        template = self.load_template(template_name)
        return self.format_template(template, **kwargs)


# Global instance for convenience
_default_loader = None


def get_prompt_loader() -> PromptLoader:
    """Get the default prompt loader instance."""
    global _default_loader
    if _default_loader is None:
        _default_loader = PromptLoader()
    return _default_loader


def load_prompt_template(template_name: str, **kwargs) -> str:
    """
    Convenience function to load and format a prompt template.

    Args:
        template_name: Name of the template file (without .yaml extension)
        **kwargs: Variable values to inject into the template

    Returns:
        Formatted prompt string
    """
    loader = get_prompt_loader()
    return loader.load_and_format(template_name, **kwargs)

"""
Configuration integration for Claimify pipeline.

This module provides integration between the main ClarifAI configuration system
and the Claimify pipeline configuration.
"""

import logging
from typing import Dict, Any, Optional
from pathlib import Path

from .data_models import ClaimifyConfig

logger = logging.getLogger(__name__)


def load_claimify_config_from_yaml(config_data: Dict[str, Any]) -> ClaimifyConfig:
    """
    Load ClaimifyConfig from YAML configuration data.
    
    Args:
        config_data: Dictionary containing parsed YAML configuration
        
    Returns:
        ClaimifyConfig instance with settings from YAML
    """
    claimify_section = config_data.get("claimify", {})
    
    # Context window settings
    context_window = claimify_section.get("context_window", {})
    context_window_p = context_window.get("p", 3)
    context_window_f = context_window.get("f", 1)
    
    # Model settings
    models = claimify_section.get("models", {})
    selection_model = models.get("selection")
    disambiguation_model = models.get("disambiguation") 
    decomposition_model = models.get("decomposition")
    default_model = models.get("default", "gpt-3.5-turbo")
    
    # Processing settings
    processing = claimify_section.get("processing", {})
    max_retries = processing.get("max_retries", 3)
    timeout_seconds = processing.get("timeout_seconds", 30)
    temperature = processing.get("temperature", 0.1)
    max_tokens = processing.get("max_tokens", 1000)
    
    # Threshold settings
    thresholds = claimify_section.get("thresholds", {})
    selection_confidence_threshold = thresholds.get("selection_confidence", 0.5)
    disambiguation_confidence_threshold = thresholds.get("disambiguation_confidence", 0.5)
    decomposition_confidence_threshold = thresholds.get("decomposition_confidence", 0.5)
    
    # Logging settings
    logging_config = claimify_section.get("logging", {})
    log_decisions = logging_config.get("log_decisions", True)
    log_transformations = logging_config.get("log_transformations", True)
    log_timing = logging_config.get("log_timing", True)
    
    return ClaimifyConfig(
        context_window_p=context_window_p,
        context_window_f=context_window_f,
        selection_model=selection_model,
        disambiguation_model=disambiguation_model,
        decomposition_model=decomposition_model,
        default_model=default_model,
        max_retries=max_retries,
        timeout_seconds=timeout_seconds,
        temperature=temperature,
        max_tokens=max_tokens,
        selection_confidence_threshold=selection_confidence_threshold,
        disambiguation_confidence_threshold=disambiguation_confidence_threshold,
        decomposition_confidence_threshold=decomposition_confidence_threshold,
        log_decisions=log_decisions,
        log_transformations=log_transformations,
        log_timing=log_timing,
    )


def load_claimify_config_from_file(config_file: Optional[str] = None) -> ClaimifyConfig:
    """
    Load ClaimifyConfig from YAML configuration file.
    
    Args:
        config_file: Path to YAML config file (optional, will search for default)
        
    Returns:
        ClaimifyConfig instance
    """
    try:
        import yaml
    except ImportError:
        logger.warning("PyYAML not available, using default Claimify configuration")
        return ClaimifyConfig()
    
    if config_file is None:
        # Look for default config file
        current_path = Path.cwd()
        search_paths = []
        
        # Priority 1: settings directory
        for path in [current_path] + list(current_path.parents):
            search_paths.append(path / "settings" / "clarifai.config.yaml")
        
        # Priority 2: root level (legacy)
        for path in [current_path] + list(current_path.parents):
            search_paths.append(path / "clarifai.config.yaml")
        
        for config_path in search_paths:
            if config_path.exists():
                config_file = str(config_path)
                break
    
    if config_file and Path(config_file).exists():
        logger.info(f"Loading Claimify configuration from {config_file}")
        try:
            with open(config_file, "r") as f:
                config_data = yaml.safe_load(f) or {}
            return load_claimify_config_from_yaml(config_data)
        except Exception as e:
            logger.error(f"Failed to load Claimify config from {config_file}: {e}")
            return ClaimifyConfig()
    else:
        logger.info("No configuration file found, using default Claimify configuration")
        return ClaimifyConfig()


def get_model_config_for_stage(config_data: Dict[str, Any], stage: str) -> str:
    """
    Get the configured model for a specific Claimify stage.
    
    Args:
        config_data: Configuration dictionary
        stage: Stage name ("selection", "disambiguation", "decomposition")
        
    Returns:
        Model name for the stage
    """
    claimify_config = config_data.get("claimify", {})
    models = claimify_config.get("models", {})
    
    # Get stage-specific model or fall back to default
    stage_model = models.get(stage)
    if stage_model:
        return stage_model
    
    # Fall back to claimify default
    claimify_default = models.get("default")
    if claimify_default:
        return claimify_default
    
    # Fall back to global default
    llm_config = config_data.get("llm", {})
    llm_models = llm_config.get("models", {})
    return llm_models.get("default", "gpt-3.5-turbo")
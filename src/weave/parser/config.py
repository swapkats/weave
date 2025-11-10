"""Configuration file parser."""

from pathlib import Path
from typing import Any, Dict

import yaml
from pydantic import ValidationError

from ..core.exceptions import ConfigError
from ..core.models import WeaveConfig
from .env import substitute_env_vars
from .resources import ResourceProcessor


def load_config_from_path(path: Path) -> WeaveConfig:
    """
    Load and parse a Weave configuration file.

    Args:
        path: Path to .weave.yaml file

    Returns:
        Parsed WeaveConfig object

    Raises:
        ConfigError: If file not found, invalid YAML, or validation fails
    """
    if not path.exists():
        raise ConfigError(
            f"Configuration file not found: {path}\n"
            f"Run 'weave init' to create a new configuration."
        )

    try:
        with open(path, "r") as f:
            raw_content = f.read()
    except Exception as e:
        raise ConfigError(f"Failed to read config file: {e}")

    return load_config(raw_content, str(path), config_path=path)


def load_config(content: str, source: str = "<string>", config_path: Path = None) -> WeaveConfig:
    """
    Parse Weave configuration from string.

    Args:
        content: YAML content as string
        source: Source name for error messages
        config_path: Optional path to config file (for resource loading)

    Returns:
        Parsed WeaveConfig object

    Raises:
        ConfigError: If invalid YAML or validation fails
    """
    # Substitute environment variables
    try:
        substituted = substitute_env_vars(content, strict=True)
    except ValueError as e:
        raise ConfigError(f"Environment variable error: {e}")

    # Parse YAML
    try:
        data: Dict[str, Any] = yaml.safe_load(substituted)
    except yaml.YAMLError as e:
        raise ConfigError(f"Invalid YAML in {source}:\n{e}")

    if not isinstance(data, dict):
        raise ConfigError(f"Config must be a YAML mapping, got {type(data).__name__}")

    # Process resource references
    if config_path:
        try:
            processor = ResourceProcessor(config_path)
            data = processor.process_config(data)
        except Exception as e:
            # Resource loading is non-critical, log warning but continue
            import warnings
            warnings.warn(f"Failed to process resources: {e}")

    # Validate with Pydantic
    try:
        config = WeaveConfig(**data)
    except ValidationError as e:
        # Format Pydantic errors nicely
        errors = []
        for error in e.errors():
            loc = " -> ".join(str(x) for x in error["loc"])
            msg = error["msg"]
            errors.append(f"  • {loc}: {msg}")

        error_text = "\n".join(errors)
        raise ConfigError(f"Configuration validation failed:\n{error_text}")

    return config

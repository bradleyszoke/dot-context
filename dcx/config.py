"""Configuration handling for dot-context."""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from rich.console import Console

console = Console()

DEFAULT_CONFIG_FILE = ".context"


def find_config_file(start_dir: Optional[Path] = None) -> Optional[Path]:
    """
    Find the closest .context file by walking up directories.

    Args:
        start_dir: The directory to start searching from. Defaults to current directory.

    Returns:
        Path to the .context file if found, None otherwise.
    """
    if start_dir is None:
        start_dir = Path.cwd()

    current_dir = start_dir.absolute()

    # Walk up directory hierarchy until we find a .context file or hit root
    while current_dir != current_dir.parent:
        config_path = current_dir / DEFAULT_CONFIG_FILE
        if config_path.exists():
            return config_path
        current_dir = current_dir.parent

    # Check root directory as well
    config_path = current_dir / DEFAULT_CONFIG_FILE
    if config_path.exists():
        return config_path

    return None


def load_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load configuration from a .context file.

    Args:
        config_path: Path to the .context file. If None, will search for one.

    Returns:
        Dictionary containing the parsed configuration.

    Raises:
        FileNotFoundError: If no .context file is found.
        yaml.YAMLError: If the .context file is not valid YAML.
    """
    if config_path is None:
        config_path = find_config_file()

    if config_path is None or not config_path.exists():
        raise FileNotFoundError(f"No {DEFAULT_CONFIG_FILE} file found.")

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        # Expand any environment variables in the config
        config = _expand_env_vars(config)
        return config
    except yaml.YAMLError as e:
        console.print(f"[bold red]Error parsing {config_path}:[/bold red]")
        console.print(f"[red]{str(e)}[/red]")
        raise


def _expand_env_vars(config_item):
    """
    Recursively expand environment variables in configuration values.

    Environment variables should be in the format ${VAR_NAME}.
    """
    if isinstance(config_item, dict):
        return {k: _expand_env_vars(v) for k, v in config_item.items()}
    if isinstance(config_item, list):
        return [_expand_env_vars(i) for i in config_item]
    if isinstance(config_item, str):
        # Expand ${VAR_NAME} syntax to environment variable values
        if "${" in config_item and "}" in config_item:
            start = config_item.find("${")
            end = config_item.find("}", start)
            if end > start >= 0:
                env_var = config_item[start + 2 : end]
                env_val = os.environ.get(env_var, "")
                return config_item[:start] + env_val + config_item[end + 1 :]
        return config_item

    return config_item

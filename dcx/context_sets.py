"""Context set management for dot-context."""

import glob
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from rich.console import Console

from .config import load_config, find_config_file

console = Console()


class ContextSet:
    """Represents a set of context files."""

    def __init__(self, name: str, config: Dict[str, Any], base_dir: Path):
        """
        Initialize a context set.

        Args:
            name: The name of the context set
            config: The configuration dictionary for this set
            base_dir: The base directory to resolve relative paths against
        """
        self.name = name
        self.description = config.get("description", "")
        self.match_patterns = config.get("match", [])
        self.includes = config.get("include", [])
        self.base_dir = base_dir

    def get_matching_files(
        self, all_sets: Optional[Dict[str, "ContextSet"]] = None
    ) -> List[Path]:
        """
        Get all files matching this context set's patterns.

        Args:
            all_sets: Dictionary of all available context sets, for resolving includes

        Returns:
            List of file paths matching this context set
        """
        matching_files = set()

        # Process direct match patterns
        for pattern in self.match_patterns:
            # Ensure the pattern is relative to the base directory
            full_pattern = os.path.join(self.base_dir, pattern)
            for file_path in glob.glob(full_pattern, recursive=True):
                if os.path.isfile(file_path):
                    matching_files.add(Path(file_path))

        # Process included sets if provided
        if all_sets is not None:
            for include_name in self.includes:
                if include_name in all_sets:
                    included_set = all_sets[include_name]
                    # Avoid circular includes by not passing all_sets down
                    if include_name != self.name:
                        included_files = included_set.get_matching_files()
                        matching_files.update(included_files)
                else:
                    console.print(
                        f"[yellow]Warning:[/yellow] Included set '{include_name}' not found"
                    )

        return sorted(list(matching_files))


def load_context_sets(config_path: Optional[Path] = None) -> Dict[str, ContextSet]:
    """
    Load all context sets from the configuration.

    Args:
        config_path: Path to the .context file. If None, will search for one.

    Returns:
        Dictionary mapping set names to ContextSet objects
    """
    if config_path is None:
        config_path = find_config_file()
        if config_path is None:
            raise FileNotFoundError("No .context file found.")

    config_data = load_config(config_path)
    base_dir = config_path.parent

    context_sets = {}
    sets_config = config_data.get("Sets", {})

    for set_name, set_config in sets_config.items():
        context_sets[set_name] = ContextSet(set_name, set_config, base_dir)

    return context_sets


def get_context_set_files(
    set_name: str, config_path: Optional[Path] = None
) -> List[Path]:
    """
    Get all files for a specific context set.

    Args:
        set_name: Name of the context set to retrieve
        config_path: Path to the .context file. If None, will search for one.

    Returns:
        List of file paths in the context set

    Raises:
        KeyError: If the requested set does not exist
    """
    context_sets = load_context_sets(config_path)

    if set_name not in context_sets:
        raise KeyError(f"Context set '{set_name}' not found")

    return context_sets[set_name].get_matching_files(context_sets)

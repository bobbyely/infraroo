"""
Configuration loader for Infraroo.
"""

from pathlib import Path
from typing import Any

import yaml


def find_project_root() -> Path:
    """
    Find project root by looking for config/ directory.

    Searches upward from current directory until it finds a directory
    containing a 'config' subdirectory.

    Returns:
        Path to project root

    Raises:
        FileNotFoundError: If project root cannot be found
    """
    current = Path.cwd()
    while current != current.parent:
        if (current / "config").is_dir():
            return current
        current = current.parent
    raise FileNotFoundError("Could not find project root (no config/ directory found)")


class Config:
    """Configuration loader and accessor."""

    def __init__(self, config_path: str = "config/config.yaml"):
        """
        Load configuration from YAML file.

        Args:
            config_path: Path to config file (relative to project root)
        """
        project_root = find_project_root()
        full_path = project_root / config_path

        if not full_path.exists():
            raise FileNotFoundError(f"Config file not found: {full_path}")

        with open(full_path) as f:
            self._config = yaml.safe_load(f)

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.

        Args:
            key_path: Dot-separated path (e.g., 'data.download.zoom')
            default: Default value if key not found

        Returns:
            Configuration value

        Example:
            >>> config = Config()
            >>> config.get('data.download.zoom')
            20
        """
        keys = key_path.split(".")
        value = self._config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    @property
    def download_zoom(self) -> int:
        """Get download zoom level."""
        return self.get("data.download.zoom", 20)

    @property
    def download_size(self) -> int:
        """Get download image size."""
        return self.get("data.download.size", 640)

    @property
    def output_dir(self) -> str:
        """Get output directory for downloaded images."""
        return self.get("data.download.output_dir", "data/raw")


def load_config(config_path: str = "config/config.yaml") -> Config:
    """
    Load configuration from file.

    Args:
        config_path: Path to config file (relative to project root)

    Returns:
        Config object
    """
    return Config(config_path)

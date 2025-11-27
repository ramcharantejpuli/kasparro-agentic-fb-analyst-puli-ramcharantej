"""Configuration loader utility."""
import yaml
from pathlib import Path
from typing import Any, Dict


def load_config(config_path: str = "config/config.yaml") -> Dict[str, Any]:
    """Load configuration from YAML file."""
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    return config


def get_data_path(config: Dict[str, Any]) -> str:
    """Get the appropriate data path based on config."""
    if config['data']['use_sample']:
        return config['data']['sample_path']
    return config['data']['csv_path']

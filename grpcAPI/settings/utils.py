import importlib.util
import json
import logging
import os
import sys
from pathlib import Path

import toml
import yaml
from typing_extensions import Any, Dict, Optional

DEFAULT_CONFIG_PATH = Path("./grpcAPI/settings/config.json")

logger = logging.getLogger(__name__)


def resolve_config_path(
    cli_arg: Optional[str] = None, env_var: str = "GRPCAPI_CONFIG"
) -> Optional[Path]:
    """
    Resolves the configuration file path with the following priority:
    1. CLI argument
    2. Environment variable
    3. Default path (if exists)
    """
    if cli_arg:
        return Path(cli_arg)

    env_path = os.getenv(env_var)
    if env_path:
        return Path(env_path)

    if DEFAULT_CONFIG_PATH.exists():
        return DEFAULT_CONFIG_PATH

    return None


def load_file_by_extension(path: Path) -> Dict[str, Any]:
    """
    Loads and parses a config file based on its file extension.
    Supports: .toml, .yaml/.yml, .json
    """
    try:
        ext = path.suffix.lower()
        with path.open("r", encoding="utf-8") as f:
            if ext == ".toml":
                return toml.load(f)
            elif ext in (".yaml", ".yml"):
                return yaml.safe_load(f)
            elif ext == ".json":
                return json.load(f)
            else:
                raise ValueError("Unsupported config file format: {}".format(ext))
    except Exception as e:
        logger.error(f"Failed to parse config: {str(e)}")
        return {}


def load_config(
    config_arg: Optional[str] = None, field: Optional[str] = None
) -> Dict[str, Any]:
    """
    Loads the configuration and optionally extracts a specific section.
    """
    config_path = resolve_config_path(config_arg)

    if config_path and config_path.exists():
        logger.info(f"Loading config from: {config_path}")
        settings = load_file_by_extension(config_path)
        return settings.get(field, {}) if field else settings

    logger.info("No config found. Using defaults.")
    return {}


def combine_settings(
    user_settings: Dict[str, Any],
    field: Optional[str] = None,
    default_path: Path = DEFAULT_CONFIG_PATH,
) -> Dict[str, Any]:
    """
    Merges default settings with user-provided settings.
    If 'field' is defined, merges only that section.
    """
    default_settings = load_file_by_extension(default_path)

    if field:
        default_settings = default_settings.get(field, {})
        user_settings = user_settings.get(field, {})

    return {**default_settings, **user_settings}


def load_app(app_path: str) -> None:
    """
    Dynamically imports a Python module from the given file path.
    """
    path = Path(app_path)
    if not path.exists():
        raise FileNotFoundError("❌ App path not found: {}".format(app_path))

    spec = importlib.util.spec_from_file_location("app_module", path)
    if spec is None or spec.loader is None:
        raise ImportError("❌ Could not load module from: {}".format(app_path))

    app_module = importlib.util.module_from_spec(spec)
    sys.modules["app_module"] = app_module
    spec.loader.exec_module(app_module)
    logger.info(f"App loaded: {app_path}")


if __name__ == "__main__":
    config = load_config()
    logger.info(config)

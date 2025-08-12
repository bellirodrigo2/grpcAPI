import importlib.util
import logging
import sys
from pathlib import Path

import json5
import toml
import yaml
from typing_extensions import Any, Dict


DEFAULT_CONFIG_PATH = Path("./grpcAPI/commands/settings/config.json")

logger = logging.getLogger(__name__)


def load_file_by_extension(path: Path) -> Dict[str, Any]:
    """
    Loads and parses a config file based on its file extension.
    Supports: .toml, .yaml/.yml, .json (with comments support)
    """
    try:
        ext = path.suffix.lower()
        if ext == ".toml":
            with path.open("r", encoding="utf-8") as f:
                return toml.load(f)
        elif ext in (".yaml", ".yml"):
            with path.open("r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        elif ext == ".json":
            # Use JSON5 parser for JSON with comments support
            with path.open("r", encoding="utf-8") as f:
                return json5.load(f)
        else:
            raise ValueError("Unsupported config file format: {}".format(ext))
    except Exception as e:
        logger.error(f"Failed to parse config: {str(e)}")
        return {}


def combine_settings(
    user_settings: Dict[str, Any],
    default_path: Path = DEFAULT_CONFIG_PATH,
) -> Dict[str, Any]:
    """
    Merges default settings with user-provided settings.
    If 'field' is defined, merges only that section.
    """
    default_settings = load_file_by_extension(default_path)

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

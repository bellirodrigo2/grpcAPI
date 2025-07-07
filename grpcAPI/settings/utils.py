import importlib.util
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import toml

str_settings_path = "./grpcAPI/settings/config.toml"


def load_config(
    config_arg: Optional[str] = None, field: Optional[str] = None
) -> Dict[str, Any]:
    std = Path(str_settings_path)
    if config_arg is not None:
        config_path = Path(config_arg)
    elif os.getenv("GRPCAPI_CONFIG"):
        config_path = Path(os.getenv("GRPCAPI_CONFIG"))
    elif std.exists():
        config_path = std
    else:
        config_path = None

    if config_path and config_path.exists():
        print(f"Loading config from {config_path}")
        settings = toml.load(config_path)
        if field is not None and field in settings:
            return settings.get(field, {})
        return settings
    else:
        print("No config found, using defaults")
        return {}


def combine_settings(
    user_settings: Dict[str, Any],
    field: Optional[str] = None,
    std_settings_path: str = str_settings_path,
) -> Dict[str, Any]:

    std_settings: Dict[str, Any] = toml.load(std_settings_path)
    std_settings = std_settings.get(field)

    if field in user_settings:
        user_settings = user_settings.get(field)
    return {**std_settings, **user_settings}


def load_app(app_path: str) -> None:
    spec = importlib.util.spec_from_file_location("app_module", app_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load app module from {app_path}")
    app_module = importlib.util.module_from_spec(spec)
    sys.modules["app_module"] = app_module

    spec.loader.exec_module(app_module)


if __name__ == "__main__":

    config = load_config()
    print(config)

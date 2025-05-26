import importlib.util
from typing import Any, Callable, Dict, List

import toml

from grpcAPI.app import App
from grpcAPI.makeproto.main import compile_packs
from grpcAPI.types import Context


def placeholder(func: Callable[..., Any]) -> List[str]:
    return []


def load_app(app_path: str) -> None:
    spec = importlib.util.spec_from_file_location("app_module", app_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load app module from {app_path}")

    app_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(app_module)


def compile_app(app_path: str, version: str, user_settings: Dict[str, Any]) -> None:

    load_app(app_path)

    app = App()

    std_settings: Dict[str, Any] = toml.load("./config.toml")
    app_settings: Dict[str, Any] = {
        "custompass": placeholder,
        "extra_args": [Context],
    }

    user_settings = user_settings or {}
    settings = {**std_settings, **app_settings, **user_settings}

    ignore_instance = []

    compile_packs(app.packages, settings, version, ignore_instance)

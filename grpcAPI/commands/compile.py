import importlib.util
from pathlib import Path
from typing import Any, Callable, Dict, List

import toml

from grpcAPI import App
from grpcAPI.makeproto import make_protos

# from grpcAPI.ctxinject.validate import func_signature_validation
from grpcAPI.proto_schema import persist_protos
from grpcAPI.types import Context


# func_signature_validation
# fazer partial com Context
def placeholder(func: Callable[..., Any]) -> List[str]:
    return []


def load_app(app_path: str) -> None:
    spec = importlib.util.spec_from_file_location("app_module", app_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load app module from {app_path}")

    app_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(app_module)


def compile_proto(
    app_path: str, version_mode: str, user_settings: Dict[str, Any]
) -> None:

    load_app(app_path)

    # FALTA FAZER APP singleton
    app = App()

    std_settings: Dict[str, Any] = toml.load("./config.toml")
    app_settings: Dict[str, Any] = {
        "custompass": placeholder,
        "extra_args": [Context],
    }

    user_settings = user_settings or {}
    settings = {**std_settings, **app_settings, **user_settings}

    # Depends, ModelMethodField e ModelMethodInj para FromRequest e FromContext
    ignore_instance = []

    packs = app.packages
    protos_dict = make_protos(packs, settings, ignore_instance)
    if protos_dict is None:
        # COMPILATION FAIL
        return

    output_dir = Path(settings.get("output_dir", "grpcAPI/proto"))

    if version_mode is "lint":
        print(f"[INFO] Lint mode: no files will be written.")
        return

    try:
        persist_protos(
            output_dir,
            version_mode,
            protos_dict,
            packs,
        )

    except Exception as e:
        print(f"[ERROR] Failed to persist proto files:\n {e}")
        raise

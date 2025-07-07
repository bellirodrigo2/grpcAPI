from pathlib import Path
from typing import Any, Dict

from grpcAPI.app import App
from grpcAPI.proto_builder import build_protos
from grpcAPI.proto_schema import persist_protos
from grpcAPI.settings.utils import combine_settings, load_app


def get_output_dir(settings: Dict[str, str]) -> Path:
    output_dir = Path(settings.get("output_dir", "./grpcAPI/proto"))
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def compile_proto(
    app_path: str, version_mode: str, user_settings: Dict[str, Any]
) -> None:

    settings = combine_settings(user_settings, "compile")

    load_app(app_path)
    app = App()

    protos_dict = build_protos(app, settings)
    if protos_dict is None:
        # COMPILATION FAIL
        return

    output_dir = get_output_dir(settings)

    if version_mode == "lint":
        print("[INFO] Lint mode: no files will be written.")
        return

    try:
        packs = app.packages
        persist_protos(
            output_dir,
            version_mode,
            protos_dict,
            packs,
        )

    except Exception as e:
        print(f"[ERROR] Failed to persist proto files:\n {e}")
        raise

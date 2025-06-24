from functools import partial
from pathlib import Path
from typing import Any, Dict

import toml

from grpcAPI import App
from grpcAPI.commands.utils import load_app
from grpcAPI.makeproto import make_protos
from grpcAPI.proto_inject import extract_request, validate_injectable_function
from grpcAPI.proto_schema import persist_protos


def compile_proto(
    app_path: str, version_mode: str, user_settings: Dict[str, Any]
) -> None:

    load_app(app_path)

    app = App()

    std_settings: Dict[str, Any] = toml.load("./grpcAPI/commands/config.toml")

    user_settings = user_settings or {}
    settings = {**std_settings, **user_settings}

    packs = app.packages

    # add caster do signature check
    p = validate_injectable_function
    caster_tuples = list(app._caster.keys())
    validate_injectable_function_wrapper = partial(
        p.func, *p.args, **p.keywords, type_cast=caster_tuples
    )
    protos_dict = make_protos(
        packs, settings, validate_injectable_function_wrapper, extract_request
    )
    if protos_dict is None:
        # COMPILATION FAIL
        return

    output_dir = Path(settings.get("output_dir", "./grpcAPI/proto"))
    output_dir.mkdir(parents=True, exist_ok=True)
    if version_mode == "lint":
        print("[INFO] Lint mode: no files will be written.")
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

from functools import partial
from pathlib import Path
from typing import Any, Callable, Dict

import toml

from grpcAPI import App
from grpcAPI.commands.utils import combine_settings, load_app
from grpcAPI.makeproto import make_protos
from grpcAPI.proto_inject import extract_request, validate_injectable_function
from grpcAPI.proto_schema import persist_protos


def get_output_dir(settings: Dict[str, str]) -> Path:
    output_dir = Path(settings.get("output_dir", "./grpcAPI/proto"))
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def define_validation_function(app: App) -> Callable[..., Any]:
    p = validate_injectable_function
    caster_tuples = list(app._caster.keys())
    return partial(p.func, *p.args, **p.keywords, type_cast=caster_tuples)


def compile_proto(
    app_path: str, version_mode: str, user_settings: Dict[str, Any]
) -> None:

    settings = combine_settings(
        "./grpcAPI/commands/config.toml", user_settings, "compile"
    )

    load_app(app_path)
    app = App()

    validate_function = define_validation_function(app)

    packs = app.packages
    protos_dict = make_protos(packs, settings, validate_function, extract_request)
    if protos_dict is None:
        # COMPILATION FAIL
        return

    output_dir = get_output_dir(settings)

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

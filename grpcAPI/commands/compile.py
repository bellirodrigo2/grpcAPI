import importlib.util
import re
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import toml

from grpcAPI.app import App

# from grpcAPI.ctxinject.validate import func_signature_validation
from grpcAPI.makeproto.main import make_protos
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

    app = App()

    std_settings: Dict[str, Any] = toml.load("./config.toml")
    app_settings: Dict[str, Any] = {
        "custompass": placeholder,
        "extra_args": [Context],
    }

    user_settings = user_settings or {}
    settings = {**std_settings, **app_settings, **user_settings}

    # Depends e ModelMethodInj para o FromContext
    ignore_instance = []

    packs = app.packages
    protos_dict = make_protos(packs, settings, ignore_instance)
    if protos_dict is None:
        return

    if version_mode == "lint":
        print("[LINT] Compilation passed successfully. No files written.")
        return

    output_dir = Path(settings.get("output_dir", "grpcAPI/proto"))

    output_subdir = determine_output_subdir(output_dir, mode=version_mode)

    if output_subdir is not None:
        write_modules_to_files(protos_dict, output_subdir)


def write_modules_to_files(
    modules: Dict[str, Dict[str, str]],
    output_dir: Path,
) -> None:
    for package, proto_dict in modules.items():
        package_path = output_dir / package
        package_path.mkdir(parents=True, exist_ok=True)

        for modulename, proto_text in proto_dict.items():
            filename = f"{modulename}.proto"
            proto_path = package_path / filename

            with open(proto_path, "w", encoding="utf-8") as f:
                f.write(proto_text)

            print(f"Wrote proto file: {proto_path}")


def determine_output_subdir(
    output_dir: Path,
    mode: str = "new",
) -> Optional[Path]:
    if mode == "new":
        versions = []
        for child in output_dir.iterdir():
            if child.is_dir() and re.match(r"^V\d+$", child.name):
                version_num = int(child.name[1:])
                versions.append(version_num)
        next_version = max(versions, default=0) + 1
        target_dir = output_dir / f"V{next_version}"
        print(f"[INFO] Creating new version directory: {target_dir}")

    elif mode == "overwrite":
        versions = []
        for child in output_dir.iterdir():
            if child.is_dir() and re.match(r"^V\d+$", child.name):
                version_num = int(child.name[1:])
                versions.append(version_num)
        if not versions:
            raise ValueError("No existing version found to overwrite.")
        last_version = max(versions)
        target_dir = output_dir / f"V{last_version}"
        print(f"[INFO] Overwriting last version directory: {target_dir}")

    elif mode == "draft":
        target_dir = output_dir / "draft"
        print(f"[INFO] Using draft directory: {target_dir}")

    elif mode == "temporary":
        target_dir = output_dir / "tmp"
        print(f"[INFO] Using temporary directory: {target_dir}")

    elif mode == "lint":
        print(f"[INFO] Lint mode: no files will be written.")
        return None

    else:
        raise ValueError(f"Unknown mode: {mode}")

    target_dir.mkdir(parents=True, exist_ok=True)
    return target_dir

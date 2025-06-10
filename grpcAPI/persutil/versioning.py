import re
from pathlib import Path
from typing import Tuple, Union


def schema_file_name(word: str) -> str:
    return f"schema.v{word}.json"


def get_current_snapshot_version(
    base_path: Path,
) -> int:
    existing = list(base_path.glob(schema_file_name("*")))
    versions = [f.stem.split(".v")[-1] for f in existing if ".v" in f.stem]
    versions_int = [int(v) for v in versions if v.isdigit()]
    return max(versions_int, default=0)


def get_current_folder_version(
    base_path: Path,
) -> int:
    versions: list[int] = []
    for child in base_path.iterdir():
        if child.is_dir() and re.match(r"^V\d+$", child.name):
            version_num = int(child.name[1:])
            versions.append(version_num)
    return max(versions, default=0)


def get_current_version(
    base_path: Path,
) -> int:
    current_snapshot = get_current_snapshot_version(base_path)
    current_folder = get_current_folder_version(base_path)

    if current_snapshot != current_folder:
        raise ValueError(
            "Snapshot version and folder version do not match. Please ensure they are synchronized."
        )
    return current_snapshot


def get_next_version(
    base_path: Path,
) -> int:
    current_version = get_current_version(base_path)
    next_version = current_version + 1
    return next_version


def get_folder_path(base_path: Path, version: Union[int, str]) -> Path:
    version = version if isinstance(version, str) else f"V{version}"
    return base_path / version


def define_version_mode(base_path: Path, mode: str) -> Union[str, int]:

    if mode == "new":
        version = get_next_version(base_path)

    elif mode == "overwrite":
        version = get_current_version(base_path)

    elif mode == "draft":
        version = mode

    else:
        raise ValueError(f"Unknown mode: {mode}")

    return version


def get_version_paths(base_path: Path, mode: str) -> Tuple[Path, str]:

    version = define_version_mode(base_path, mode)

    target_dir = get_folder_path(base_path, version)

    snapshot_path = schema_file_name(str(version))

    return target_dir, snapshot_path

import re
from pathlib import Path
from typing import Tuple, Union


def schema_file_name(word: str) -> str:
    return f"schema.v{word}.json"


schema_folder = "schema"


def get_current_snapshot_version(
    base_path: Path,
) -> int:
    schema_dir = base_path / schema_folder
    existing = list(schema_dir.glob(schema_file_name("*")))
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
            f"Snapshot version and folder version do not match. Please ensure they are synchronized. {current_snapshot} vs {current_folder}"
        )
    return current_snapshot


def get_next_version(
    base_path: Path,
) -> int:
    current_version = get_current_version(base_path)
    next_version = current_version + 1
    return next_version


def define_version_mode(base_path: Path, mode: str) -> Union[str, int]:

    mode = mode.upper()

    if mode == "NEW":
        version = get_next_version(base_path)

    elif mode == "OVERWRITE":
        version = get_current_version(base_path)

    elif mode == "DRAFT":
        version = mode

    else:
        raise ValueError(f"Unknown mode: {mode}")

    return version


def get_folder_path(version: Union[int, str]) -> str:
    version = version if isinstance(version, str) else f"V{version}"
    return version


def get_snapshot_path(version: Union[int, str]) -> Tuple[str, str]:
    snapshot_file = schema_file_name(str(version))
    return schema_folder, snapshot_file


def get_version_paths(base_path: Path, mode: str) -> Tuple[str, Tuple[str, str]]:

    version = define_version_mode(base_path, mode)

    target_dir = get_folder_path(version)

    if (base_path / target_dir).exists() and mode == "new":
        raise FileExistsError(
            f"Directory {target_dir} already exists. Use 'overwrite' mode to replace it."
        )

    schema_folder, schema_file = get_snapshot_path(version)
    snapshot_path = base_path / schema_folder / schema_file
    if snapshot_path.exists() and mode == "new":
        raise FileExistsError(
            f"Snapshot file {snapshot_path} already exists. Use 'overwrite' mode to replace it."
        )
    return target_dir, (schema_folder, schema_file)

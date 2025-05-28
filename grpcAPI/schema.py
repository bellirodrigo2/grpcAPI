import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Generic, Protocol, TypeVar

from deepdiff import DeepDiff

T = TypeVar("T", covariant=True)


class ISchema(Protocol, Generic[T]):
    def serialize(self) -> T: ...
    def hash(self) -> str: ...


def save_snapshot(schema: ISchema[T], path: Path) -> None:
    serialized = schema.serialize()
    digest = schema.hash()
    snapshot = {
        "hash": digest,
        "schema": serialized,
    }
    path.write_text(json.dumps(snapshot, indent=2, sort_keys=True))


def save_snapshot_versioned(
    schema: ISchema[T],
    base_path: Path,
    new_version: bool = False,
    overwrite: bool = False,
) -> Path:
    base_path.mkdir(parents=True, exist_ok=True)

    if new_version:
        existing = list(base_path.glob("model_snapshot.v*.json"))
        versions = [int(f.stem.split(".v")[-1]) for f in existing if ".v" in f.stem]
        next_version = max(versions or [0]) + 1
        filename = base_path / f"model_snapshot.v{next_version}.json"
    else:
        filename = base_path / "model_snapshot.v1.json"

        if filename.exists() and not overwrite:
            raise FileExistsError(
                f"Snapshot already exists at {filename}. Use overwrite=True or new_version=True."
            )

    save_snapshot(schema, filename)
    return filename


def validate_snapshot(schema: ISchema[T], path: Path) -> None:
    current_serialized = schema.serialize()
    current_hash = schema.hash()

    saved = json.loads(path.read_text())
    saved_hash = saved["hash"]
    saved_schema = saved["schema"]

    if current_hash != saved_hash:
        diff = DeepDiff(saved_schema, current_serialized, verbose_level=2)
        diff_json = diff.to_json(indent=2)
        raise RuntimeError(
            f"Model does not match the compiled schema snapshot.\nDiff:\n{diff_json}"
        )

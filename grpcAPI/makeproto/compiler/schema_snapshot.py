import hashlib
import json
from pathlib import Path
from typing import Any, Dict

from deepdiff import DeepDiff
from makeproto.block_models import Block, ProtoBlocks


def serialize_block(block: Block) -> Dict[str, Any]:
    return {
        "name": block.name,
        "fields": sorted(
            [
                {"name": f.name, "type": f.ftype, "number": f.number}
                for f in block.fields
            ],
            key=lambda x: x["number"],
        ),
        "comment": block.comment,
        "options": block.options,
        "reserved_indexes": sorted(block.reserved_index),
        "reserved_names": sorted(block.reserved_keys),
    }


def serialize_proto(proto: ProtoBlocks) -> dict[str, Any]:
    return {
        "version": proto.version,
        "protofile": proto.protofile,
        "package": proto.package,
        "imports": sorted(proto.imports),
        "options": dict(sorted(proto.options.items())),
        "comment": proto.comment,
        "blocks": {
            block.name: serialize_block(block)
            for block in sorted(proto.blocks, key=lambda b: b.name)
        },
    }


def hash_proto(data: Dict[str, Any]) -> str:
    raw = json.dumps(data, sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()


def save_snapshot(proto: ProtoBlocks, path: Path) -> None:
    schema = serialize_proto(proto)
    digest = hash_proto(schema)
    snapshot = {
        "hash": digest,
        "schema": schema,
    }
    path.write_text(json.dumps(snapshot, indent=2, sort_keys=True))


def save_snapshot_versioned(
    proto: ProtoBlocks,
    base_path: Path,
    new_version: bool = False,
    overwrite: bool = False,
) -> Path:
    # Diretório para snapshots
    base_path.mkdir(parents=True, exist_ok=True)

    if new_version:
        # Lista versões existentes
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

    save_snapshot(proto, filename)
    print(f"✅ Snapshot saved: {filename}")
    return filename


def validate_snapshot(proto: ProtoBlocks, path: Path) -> None:
    current = serialize_proto(proto)
    current_hash = hash_proto(current)

    saved = json.loads(path.read_text())
    saved_hash = saved["hash"]
    saved_schema = saved["schema"]

    if current_hash != saved_hash:
        print("❌ Snapshot mismatch!")
        diff = DeepDiff(saved_schema, current, verbose_level=2)
        print(diff.to_json(indent=2))
        raise RuntimeError("Model does not match the compiled schema snapshot.")
    else:
        print("✅ Snapshot valid and unchanged.")

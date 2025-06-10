import json
from pathlib import Path
from typing import Dict, Generic, Protocol, TypeVar, Union

from deepdiff import DeepDiff

T = TypeVar("T", covariant=True)


class ISchema(Protocol, Generic[T]):
    def serialize(self) -> T: ...
    def hash(self) -> str: ...


def create_snapshot(schema: ISchema[T]) -> Dict[str, Union[str, T]]:
    serialized: T = schema.serialize()
    digest: str = schema.hash()
    snapshot: Dict[str, Union[str, T]] = {
        "hash": digest,
        "schema": serialized,
    }
    return snapshot


def validate_snapshot(schema: ISchema[T], saved: Dict[str, Union[str, T]]) -> None:
    current_serialized = schema.serialize()
    current_hash = schema.hash()

    saved_hash = saved["hash"]
    saved_schema = saved["schema"]

    if current_hash != saved_hash:
        diff = DeepDiff(saved_schema, current_serialized, verbose_level=2)
        diff_json = diff.to_json(indent=2)
        raise RuntimeError(
            f"Model does not match the compiled schema snapshot.\nDiff:\n{diff_json}"
        )

import json
import tempfile
import unittest
from pathlib import Path
from typing import Any, Dict

from grpcAPI.schema import (
    ISchema,
    save_snapshot,
    save_snapshot_versioned,
    validate_snapshot,
)


class DummySchema(ISchema[Dict[str, Any]]):
    def __init__(self, data: Dict[str, Any]):
        self.data = data

    def serialize(self) -> Dict[str, Any]:
        return self.data

    def hash(self) -> str:
        raw = json.dumps(self.data, sort_keys=True)
        import hashlib

        return hashlib.sha256(raw.encode()).hexdigest()


class TestSnapshotUtils(unittest.TestCase):

    def setUp(self) -> None:
        self.test_dir = tempfile.TemporaryDirectory()
        self.base_path = Path(self.test_dir.name)

        self.data: Dict[str, Any] = {"field": "value", "number": 123}
        self.schema = DummySchema(self.data)

    def tearDown(self) -> None:
        self.test_dir.cleanup()

    def test_serialize_and_hash(self) -> None:
        serialized = self.schema.serialize()
        self.assertEqual(serialized, self.data)

        hash_val = self.schema.hash()
        self.assertIsInstance(hash_val, str)
        self.assertEqual(len(hash_val), 64)  # SHA256 hex length

    def test_save_snapshot(self) -> None:
        snapshot_path = self.base_path / "snapshot.json"
        save_snapshot(self.schema, snapshot_path)

        self.assertTrue(snapshot_path.exists())

        with snapshot_path.open() as f:
            saved = json.load(f)

        self.assertIn("hash", saved)
        self.assertIn("schema", saved)
        self.assertEqual(saved["schema"], self.data)

    def test_save_snapshot_versioned(self) -> None:
        versioned_path = save_snapshot_versioned(
            self.schema, self.base_path, new_version=True
        )

        self.assertTrue(versioned_path.exists())
        self.assertRegex(versioned_path.name, r"model_snapshot\.v\d+\.json")

    def test_validate_snapshot_success(self) -> None:
        snapshot_path = self.base_path / "snapshot.json"
        save_snapshot(self.schema, snapshot_path)

        try:
            validate_snapshot(self.schema, snapshot_path)
        except RuntimeError:
            self.fail("validate_snapshot raised RuntimeError unexpectedly!")

    def test_validate_snapshot_failure(self) -> None:
        snapshot_path = self.base_path / "snapshot.json"
        save_snapshot(self.schema, snapshot_path)

        altered_schema = DummySchema({"field": "new_value", "number": 123})

        with self.assertRaises(RuntimeError) as context:
            validate_snapshot(altered_schema, snapshot_path)

        self.assertIn(
            "Model does not match the compiled schema snapshot.", str(context.exception)
        )
        self.assertIn("Diff", str(context.exception))


if __name__ == "__main__":
    unittest.main()

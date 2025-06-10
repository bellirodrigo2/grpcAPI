import json
import tempfile
import unittest
from pathlib import Path
from typing import Any, Dict

from grpcAPI.persutil import ISchema, create_snapshot, validate_snapshot


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
        schema = create_snapshot(self.schema)

        self.assertIn("hash", schema)
        self.assertIn("schema", schema)

        self.assertEqual(schema["schema"], self.data)

        schema = create_snapshot(self.schema)

        try:
            validate_snapshot(self.schema, schema)
        except RuntimeError:
            self.fail("validate_snapshot raised RuntimeError unexpectedly!")

    def test_validate_snapshot_failure(self) -> None:
        schema = create_snapshot(self.schema)

        altered_schema = DummySchema({"field": "new_value", "number": 123})

        with self.assertRaises(RuntimeError) as context:
            validate_snapshot(altered_schema, schema)

        self.assertIn(
            "Model does not match the compiled schema snapshot.", str(context.exception)
        )
        self.assertIn("Diff", str(context.exception))


if __name__ == "__main__":
    unittest.main()

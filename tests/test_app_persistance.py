import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Dict
from unittest.mock import MagicMock, patch

from grpcAPI.proto_schema import persist_protos


class TestPersistProtosIntegration(unittest.TestCase):
    @patch("grpcAPI.proto_schema.create_app_schema")
    def test_persist_protos_writes_files(
        self: "TestPersistProtosIntegration", mock_create_schema: MagicMock
    ) -> None:
        mock_create_schema.return_value = '{"mock": "schema"}'

        protos_dict: Dict[str, Dict[str, str]] = {
            "foo": {
                "alpha": "syntax = 'proto3'; message A {}",
                "beta": "syntax = 'proto3'; message B {}",
            },
            "bar": {
                "gamma": "syntax = 'proto3'; message C {}",
            },
        }

        packs_list = []

        with TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)

            persist_protos(
                output_dir=output_dir,
                version_mode="new",
                protos_dict=protos_dict,
                packs_list=packs_list,
            )

            current_version = 1
            proto_dir = output_dir / f"V{current_version}"
            schema_file = output_dir / "schema" / f"schema.v{current_version}.json"

            self.assertTrue(proto_dir.exists())
            self.assertTrue(schema_file.exists())

            proto_files = list(proto_dir.rglob("*.proto"))
            self.assertEqual(len(proto_files), 3)

            with open(schema_file, "r", encoding="utf-8") as f:
                schema_content = f.read()
                self.assertEqual(schema_content, '{"mock": "schema"}')

    def test_persist_protos_overwrite(self: "TestPersistProtosIntegration") -> None:
        with TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)

            with patch("grpcAPI.proto_schema.create_app_schema") as mock_schema_1:
                mock_schema_1.return_value = '{"initial": "schema"}'
                persist_protos(
                    output_dir=output_dir,
                    version_mode="new",
                    protos_dict={"foo": {"alpha": "message A {}"}},
                    packs_list=[],
                )
            self.assertTrue((output_dir / "V1").exists())
            self.assertTrue((output_dir / "schema" / "schema.v1.json").exists())

            with patch("grpcAPI.proto_schema.create_app_schema") as mock_schema_2:
                mock_schema_2.return_value = '{"overwritten": "schema"}'
                persist_protos(
                    output_dir=output_dir,
                    version_mode="overwrite",
                    protos_dict={"foo": {"alpha": "message A { updated }"}},
                    packs_list=[],
                )

            current_version = 1
            proto_dir = output_dir / f"V{current_version}"
            schema_file = output_dir / "schema" / f"schema.v{current_version}.json"

            self.assertTrue(proto_dir.exists())
            self.assertTrue(schema_file.exists())

            proto_files = list(proto_dir.rglob("*.proto"))
            self.assertEqual(len(proto_files), 1)

            with open(schema_file, "r", encoding="utf-8") as f:
                content = f.read()
                self.assertEqual(content, '{"overwritten": "schema"}')

    def test_persist_protos_draft(self) -> None:
        with TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)

            with patch("grpcAPI.proto_schema.create_app_schema") as mock_schema:
                mock_schema.return_value = '{"draft": "schema"}'

                persist_protos(
                    output_dir=output_dir,
                    version_mode="draft",
                    protos_dict={"foo": {"drafted": "message Draft { }"}},
                    packs_list=[],
                )

            proto_dir = output_dir / "draft"
            schema_file = output_dir / "schema" / "schema.vdraft.json"

            self.assertTrue(proto_dir.exists())
            self.assertTrue(schema_file.exists())

            proto_files = list(proto_dir.rglob("*.proto"))
            self.assertEqual(len(proto_files), 1)

            content = (output_dir / "schema" / "schema.vdraft.json").read_text()
            self.assertEqual(content, '{"draft": "schema"}')


if __name__ == "__main__":
    unittest.main()

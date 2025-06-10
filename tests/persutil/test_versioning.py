import unittest
from pathlib import Path
from typing import Union
from unittest.mock import MagicMock, patch

from grpcAPI.persutil.versioning import (
    define_version_mode,
    get_current_folder_version,
    get_current_snapshot_version,
    get_current_version,
    get_folder_path,
    get_next_version,
    get_snapshot_path,
    get_version_paths,
    schema_file_name,
)


class TestVersioningFunctions(unittest.TestCase):

    def test_schema_file_name(self: "TestVersioningFunctions") -> None:
        result: str = schema_file_name("2")
        self.assertEqual(result, "schema.v2.json")

    @patch("pathlib.Path.glob")
    def test_get_current_snapshot_version(
        self: "TestVersioningFunctions", mock_glob: MagicMock
    ) -> None:
        mock_file_1 = MagicMock()
        mock_file_1.stem = "schema.v1"
        mock_file_2 = MagicMock()
        mock_file_2.stem = "schema.v3"
        mock_glob.return_value = [mock_file_1, mock_file_2]

        version: int = get_current_snapshot_version(Path())
        self.assertEqual(version, 3)

    @patch("pathlib.Path.iterdir")
    def test_get_current_folder_version(
        self: "TestVersioningFunctions", mock_iterdir: MagicMock
    ) -> None:
        mock_dir_1 = MagicMock()
        mock_dir_1.is_dir.return_value = True
        mock_dir_1.name = "V2"

        mock_dir_2 = MagicMock()
        mock_dir_2.is_dir.return_value = True
        mock_dir_2.name = "V4"

        mock_iterdir.return_value = [mock_dir_1, mock_dir_2]
        version: int = get_current_folder_version(Path())
        self.assertEqual(version, 4)

    @patch("grpcAPI.persutil.versioning.get_current_snapshot_version")
    @patch("grpcAPI.persutil.versioning.get_current_folder_version")
    def test_get_current_version_match(
        self: "TestVersioningFunctions",
        mock_folder: MagicMock,
        mock_snapshot: MagicMock,
    ) -> None:
        mock_folder.return_value = 2
        mock_snapshot.return_value = 2

        version: int = get_current_version(Path())
        self.assertEqual(version, 2)

    @patch("grpcAPI.persutil.versioning.get_current_snapshot_version")
    @patch("grpcAPI.persutil.versioning.get_current_folder_version")
    def test_get_current_version_mismatch(
        self: "TestVersioningFunctions",
        mock_folder: MagicMock,
        mock_snapshot: MagicMock,
    ) -> None:
        mock_folder.return_value = 2
        mock_snapshot.return_value = 3

        with self.assertRaises(ValueError):
            get_current_version(Path())

    @patch("grpcAPI.persutil.versioning.get_current_version")
    def test_get_next_version(
        self: "TestVersioningFunctions", mock_current_version: MagicMock
    ) -> None:
        mock_current_version.return_value = 5
        next_version: int = get_next_version(Path())
        self.assertEqual(next_version, 6)

    @patch("grpcAPI.persutil.versioning.get_next_version")
    @patch("grpcAPI.persutil.versioning.get_current_version")
    def test_define_version_mode(
        self: "TestVersioningFunctions",
        mock_get_current: MagicMock,
        mock_get_next: MagicMock,
    ) -> None:
        mock_get_next.return_value = 3
        new_version: Union[int, str] = define_version_mode(Path(), "new")
        self.assertEqual(new_version, 3)

        mock_get_current.return_value = 2
        overwrite_version: Union[int, str] = define_version_mode(Path(), "overwrite")
        self.assertEqual(overwrite_version, 2)

        draft_version: Union[int, str] = define_version_mode(Path(), "draft")
        self.assertEqual(draft_version, "draft")

        with self.assertRaises(ValueError):
            define_version_mode(Path(), "unknown")

    def test_get_folder_path(self: "TestVersioningFunctions") -> None:
        path1: str = get_folder_path(3)
        self.assertEqual(path1, "V3")

        path2: str = get_folder_path("draft")
        self.assertEqual(path2, "draft")

    def test_get_snapshot_path(self: "TestVersioningFunctions") -> None:
        snapshot1 = get_snapshot_path(3)
        self.assertEqual(snapshot1, ("schema", "schema.v3.json"))

        snapshot2 = get_snapshot_path("draft")
        self.assertEqual(snapshot2, ("schema", "schema.vdraft.json"))

    @patch("grpcAPI.persutil.versioning.define_version_mode")
    @patch("grpcAPI.persutil.versioning.get_folder_path")
    @patch("grpcAPI.persutil.versioning.get_snapshot_path")
    def test_get_version_paths(
        self: "TestVersioningFunctions",
        mock_snapshot_path: MagicMock,
        mock_folder_path: MagicMock,
        mock_define_version: MagicMock,
    ) -> None:
        mock_define_version.return_value = 4
        mock_folder_path.return_value = Path("/base/V4")
        mock_snapshot_path.return_value = "schema", "schema.v4.json"

        folder: Path
        snapshot: str
        folder, snapshot = get_version_paths(Path("/base"), "new")

        self.assertEqual(folder, Path("/base/V4"))
        self.assertEqual(snapshot, ("schema", "schema.v4.json"))


if __name__ == "__main__":
    unittest.main()

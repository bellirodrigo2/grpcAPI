import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from grpcAPI.persutil.atomic_write import WritePackage, write_atomic


class TestWriteAtomic(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = TemporaryDirectory()
        self.base_path = Path(self.temp_dir.name)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_write_single_file_clear_true(self) -> None:
        pkg = WritePackage("test_dir", True, [("content", "file.txt")])
        write_atomic(self.base_path, [pkg])
        result_file = self.base_path / "test_dir" / "file.txt"
        self.assertTrue(result_file.exists())
        self.assertEqual(result_file.read_text(encoding="utf-8"), "content")

    def test_write_multiple_files_same_package(self) -> None:
        contents = [
            ("one", "file1.txt"),
            ("two", "sub/file2.txt"),
        ]
        pkg = WritePackage("test_dir", True, contents)
        write_atomic(self.base_path, [pkg])
        self.assertEqual((self.base_path / "test_dir/file1.txt").read_text(), "one")
        self.assertEqual((self.base_path / "test_dir/sub/file2.txt").read_text(), "two")

    def test_clear_parent_true_removes_old_content(self) -> None:
        target_dir = self.base_path / "old"
        target_dir.mkdir()
        (target_dir / "to_delete.txt").write_text("delete me")

        pkg = WritePackage("old", True, [("new", "file.txt")])
        write_atomic(self.base_path, [pkg])

        self.assertFalse((target_dir / "to_delete.txt").exists())
        self.assertEqual((target_dir / "file.txt").read_text(), "new")

    def test_clear_parent_false_preserves_old_content(self) -> None:
        target_dir = self.base_path / "keep"
        target_dir.mkdir()
        (target_dir / "keep.txt").write_text("keep me")

        pkg = WritePackage("keep", False, [("new", "file.txt")])
        write_atomic(self.base_path, [pkg])

        self.assertTrue((target_dir / "keep.txt").exists())
        self.assertEqual((target_dir / "keep.txt").read_text(), "keep me")
        self.assertEqual((target_dir / "file.txt").read_text(), "new")

    def test_multiple_packages(self) -> None:
        pkg1 = WritePackage("a", True, [("a1", "1.txt")])
        pkg2 = WritePackage("b", True, [("b1", "2.txt")])
        write_atomic(self.base_path, [pkg1, pkg2])
        self.assertEqual((self.base_path / "a/1.txt").read_text(), "a1")
        self.assertEqual((self.base_path / "b/2.txt").read_text(), "b1")

    def test_empty_package_list(self) -> None:
        write_atomic(self.base_path, [])
        self.assertTrue(self.base_path.exists())

    def test_temp_cleanup_on_success(self) -> None:
        pkg = WritePackage("dir", True, [("data", "a.txt")])
        write_atomic(self.base_path, [pkg])
        self.assertFalse((self.base_path / "temp").exists())

    def test_rollback_on_error(self) -> None:
        # Simula erro criando arquivo onde deveria ser diretório
        (self.base_path / "temp").touch()  # Isso deve causar erro ao criar temp dir
        pkg = WritePackage("bad", True, [("data", "file.txt")])

        with self.assertRaises(OSError):
            write_atomic(self.base_path, [pkg])
        self.assertFalse((self.base_path / "temp").exists())


if __name__ == "__main__":
    unittest.main()

# unittest.TextTestRunner().run(
# unittest.TestLoader().loadTestsFromTestCase(TestWriteAtomic)
# )

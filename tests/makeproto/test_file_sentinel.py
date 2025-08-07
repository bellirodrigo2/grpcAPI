import os
import threading
from pathlib import Path
from unittest.mock import patch

import pytest

from grpcAPI.makeproto.files_sentinel import (
    cleanup_registered,
    ensure_dirs,
    register_path,
)


@pytest.fixture(autouse=True)
def reset_sentinel():
    """Reset global state before each test"""
    from grpcAPI.makeproto.files_sentinel import _created_dirs, _created_files, _lock

    with _lock:
        _created_files.clear()
        _created_dirs.clear()


def test_register_and_cleanup_file(tmp_path: Path) -> None:
    file_path = tmp_path / "testfile.txt"
    file_path.write_text("temporary content")
    assert file_path.exists()

    register_path(file_path, False)
    cleanup_registered()

    assert not file_path.exists()


def test_register_and_cleanup_directory(tmp_path: Path) -> None:
    dir_path = tmp_path / "testdir"
    dir_path.mkdir()
    assert dir_path.exists()

    register_path(dir_path, True)
    cleanup_registered()

    assert not dir_path.exists()


def test_ensure_dirs_creates_missing(tmp_path: Path) -> None:
    nested = tmp_path / "a" / "b" / "c"
    ensure_dirs(nested)

    assert nested.exists()
    assert nested.is_dir()

    cleanup_registered()
    assert not nested.exists()


def test_ensure_dirs_respects_existing(tmp_path: Path) -> None:
    base = tmp_path / "existing"
    base.mkdir()
    ensure_dirs(base)  # Should not register for deletion

    cleanup_registered()
    assert base.exists()


def test_cleanup_does_not_fail_on_nonexistent(tmp_path: Path) -> None:
    file_path = tmp_path / "ghost.txt"
    register_path(file_path, False)  # Never actually created

    try:
        cleanup_registered()  # Should not raise
    except Exception as e:
        pytest.fail(f"cleanup_registered raised: {e}")


# === NOVOS TESTES COMPLETOS ===


def test_register_path_validates_none():
    """Test that register_path raises ValueError for None path"""
    with pytest.raises(ValueError, match="Path cannot be None or empty"):
        register_path(None, False)


def test_ensure_dirs_validates_none():
    """Test that ensure_dirs raises ValueError for None path"""
    with pytest.raises(ValueError, match="Path cannot be None or empty"):
        ensure_dirs(None)


@pytest.mark.skipif(
    os.name == "nt", reason="Symlinks require admin privileges on Windows"
)
def test_symlink_cleanup(tmp_path: Path) -> None:
    """Test cleanup of symlinks to files and directories"""
    # Create target file and directory
    target_file = tmp_path / "target.txt"
    target_file.write_text("content")
    target_dir = tmp_path / "target_dir"
    target_dir.mkdir()

    # Create symlinks
    file_symlink = tmp_path / "link_to_file"
    dir_symlink = tmp_path / "link_to_dir"

    file_symlink.symlink_to(target_file)
    dir_symlink.symlink_to(target_dir)

    # Register symlinks
    register_path(file_symlink, False)
    register_path(dir_symlink, True)

    assert file_symlink.exists()
    assert dir_symlink.exists()
    assert file_symlink.is_symlink()
    assert dir_symlink.is_symlink()

    cleanup_registered()

    # Symlinks should be removed, targets should remain
    assert not file_symlink.exists()
    assert not dir_symlink.exists()
    assert target_file.exists()
    assert target_dir.exists()


@pytest.mark.skipif(
    os.name == "nt", reason="Symlinks require admin privileges on Windows"
)
def test_broken_symlink_cleanup(tmp_path: Path) -> None:
    """Test cleanup of broken symlinks"""
    target = tmp_path / "nonexistent"
    symlink = tmp_path / "broken_link"

    # Create symlink to non-existent target
    symlink.symlink_to(target)
    assert symlink.is_symlink()
    assert not symlink.exists()  # Broken symlink

    register_path(symlink, True)
    cleanup_registered()

    assert not symlink.is_symlink()


def test_directory_cleanup_order(tmp_path: Path) -> None:
    """Test that directories are cleaned up in correct order (deepest first)"""
    # Create nested structure
    deep_path = tmp_path / "a" / "b" / "c" / "d"
    ensure_dirs(deep_path)

    # Create files in various levels
    file1 = tmp_path / "a" / "file1.txt"
    file2 = tmp_path / "a" / "b" / "file2.txt"
    file3 = deep_path / "file3.txt"

    file1.write_text("1")
    file2.write_text("2")
    file3.write_text("3")

    register_path(file1, False)
    register_path(file2, False)
    register_path(file3, False)

    cleanup_registered()

    # All should be cleaned up
    assert not deep_path.exists()
    assert not (tmp_path / "a").exists()


def test_path_normalization(tmp_path: Path) -> None:
    """Test that paths are normalized (resolve duplicates)"""
    # Create directory with different path representations
    dir_path = tmp_path / "test"
    dir_path.mkdir()

    # Register same directory with different paths
    path1 = tmp_path / "test"
    path2 = tmp_path / "." / "test"
    path3 = tmp_path / "other" / ".." / "test"

    register_path(path1, True)
    register_path(path2, True)
    register_path(path3, True)

    # Should only be registered once after normalization
    from grpcAPI.makeproto.files_sentinel import _created_dirs, _lock

    with _lock:
        assert len(_created_dirs) == 1

    cleanup_registered()
    assert not dir_path.exists()


def test_concurrent_registration() -> None:
    """Test thread safety of path registration"""
    from grpcAPI.makeproto.files_sentinel import _created_files, _lock

    paths_to_register = [Path(f"/tmp/test_{i}") for i in range(100)]

    def register_paths(start_idx: int, end_idx: int):
        for i in range(start_idx, end_idx):
            register_path(paths_to_register[i], False)

    threads = []
    for i in range(0, 100, 10):
        thread = threading.Thread(target=register_paths, args=(i, i + 10))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    # All paths should be registered
    with _lock:
        assert len(_created_files) == 100


def test_cleanup_with_permission_error(tmp_path: Path) -> None:
    """Test cleanup handles permission errors gracefully"""
    file_path = tmp_path / "readonly.txt"
    file_path.write_text("content")

    register_path(file_path, False)

    # Make file read-only (simulate permission error)
    file_path.chmod(0o444)

    # Mock unlink to raise PermissionError
    with patch.object(Path, "unlink", side_effect=PermissionError("Permission denied")):
        # Should not raise, just log warning
        cleanup_registered()

    # File should still exist
    assert file_path.exists()


def test_cleanup_with_keyboard_interrupt(tmp_path: Path) -> None:
    """Test cleanup handles KeyboardInterrupt correctly"""
    file_path = tmp_path / "test_file.txt"
    file_path.write_text("content")
    register_path(file_path, False)

    with patch.object(Path, "unlink", side_effect=KeyboardInterrupt()):
        with pytest.raises(KeyboardInterrupt):
            cleanup_registered()


def test_ensure_dirs_at_root(tmp_path: Path) -> None:
    """Test ensure_dirs doesn't loop infinitely at filesystem root"""
    # This should not cause infinite loop
    ensure_dirs(tmp_path)  # Already exists

    # Test with root-like path (as much as we can in test environment)
    root_like = tmp_path / ".."
    ensure_dirs(root_like, clean=False)  # Don't register for cleanup


def test_mixed_files_and_directories(tmp_path: Path) -> None:
    """Test cleanup of mixed files and directories"""
    # Create complex structure
    base = tmp_path / "mixed"
    ensure_dirs(base)

    # Create files and subdirectories
    file1 = base / "file1.txt"
    subdir = base / "subdir"
    file2 = subdir / "file2.txt"

    file1.write_text("content1")
    subdir.mkdir()
    file2.write_text("content2")

    # Register everything
    register_path(file1, False)
    register_path(file2, False)
    register_path(subdir, True)

    cleanup_registered()

    # All should be cleaned
    assert not file1.exists()
    assert not file2.exists()
    assert not subdir.exists()
    # base directory created by ensure_dirs should also be cleaned
    assert not base.exists()


def test_cleanup_empty_sets() -> None:
    """Test cleanup works with empty file/directory sets"""
    # Should not fail with empty sets
    cleanup_registered()


def test_very_deep_directory_structure(tmp_path: Path) -> None:
    """Test cleanup of very deep directory structures"""
    # Create deep structure
    current = tmp_path
    for i in range(10):
        current = current / f"level_{i}"

    ensure_dirs(current)

    # Create file at deepest level
    deep_file = current / "deep_file.txt"
    deep_file.write_text("deep content")
    register_path(deep_file, False)

    cleanup_registered()

    # Everything should be cleaned up
    assert not (tmp_path / "level_0").exists()


def test_special_characters_in_paths(tmp_path: Path) -> None:
    """Test paths with special characters"""
    special_names = [
        "файл.txt",  # Unicode
        "file with spaces.txt",
        "file-with-dashes.txt",
        "file_with_underscores.txt",
        "file.with.dots.txt",
    ]

    for name in special_names:
        try:
            file_path = tmp_path / name
            file_path.write_text("content")
            register_path(file_path, False)
        except (OSError, UnicodeError):
            # Skip if filesystem doesn't support the character
            continue

    # Should clean up successfully
    cleanup_registered()


def test_register_path_type_mismatch_warning(tmp_path: Path, caplog) -> None:
    """Test warning when is_dir parameter doesn't match reality"""
    # Create a file but register as directory
    file_path = tmp_path / "actual_file.txt"
    file_path.write_text("content")

    # This should work but may log inconsistency
    register_path(file_path, True)  # Wrong: it's a file, not directory

    # During cleanup, it will try rmdir on a file, which should fail gracefully
    cleanup_registered()

    # File should still exist since rmdir failed
    assert file_path.exists()


@pytest.mark.parametrize("clean_flag", [True, False])
def test_ensure_dirs_clean_flag(tmp_path: Path, clean_flag: bool) -> None:
    """Test ensure_dirs respects clean flag"""
    nested = tmp_path / "test_clean" / "nested"
    ensure_dirs(nested, clean=clean_flag)

    assert nested.exists()

    cleanup_registered()

    if clean_flag:
        assert not nested.exists()
    else:
        assert nested.exists()  # Should not be cleaned up

from pathlib import Path

import pytest

from grpcAPI.files_sentinel import cleanup_registered, ensure_dirs, register_path


def test_register_and_cleanup_file(tmp_path: Path) -> None:
    file_path = tmp_path / "testfile.txt"
    file_path.write_text("temporary content")
    assert file_path.exists()

    register_path(file_path)
    cleanup_registered()

    assert not file_path.exists()


def test_register_and_cleanup_directory(tmp_path: Path) -> None:
    dir_path = tmp_path / "testdir"
    dir_path.mkdir()
    assert dir_path.exists()

    register_path(dir_path)
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
    register_path(file_path)  # Never actually created

    try:
        cleanup_registered()  # Should not raise
    except Exception as e:
        pytest.fail(f"cleanup_registered raised: {e}")

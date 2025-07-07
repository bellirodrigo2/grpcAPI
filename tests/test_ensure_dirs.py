# tests/test_ensure_dirs.py
import pytest

import grpcAPI.files_sentinel as sentinel
from grpcAPI.files_sentinel import ensure_dirs


@pytest.fixture(autouse=True)
def clear_sentinel_registry():
    # Clear any existing registrations before each test
    sentinel._created_dirs.clear()
    yield
    sentinel._created_dirs.clear()


def test_ensure_creates_single_directory(tmp_path, monkeypatch):
    # Target does not exist
    target = tmp_path / "a"
    assert not target.exists()

    captured = []
    monkeypatch.setattr(sentinel, "register_path", lambda p: captured.append(p))

    ensure_dirs(target)

    # Directory must now exist
    assert target.exists() and target.is_dir()
    # Exactly one registration
    assert captured == [target]


def test_ensure_creates_nested_directories(tmp_path, monkeypatch):
    # Create only tmp_path/a
    a = tmp_path / "a"
    a.mkdir()
    b_c = tmp_path / "a" / "b" / "c"
    assert not b_c.exists()

    captured = []
    monkeypatch.setattr(sentinel, "register_path", lambda p: captured.append(p))

    ensure_dirs(b_c)

    # b and c were created; a already existed
    assert b_c.exists()
    assert set(captured) == {tmp_path / "a" / "b", tmp_path / "a" / "b" / "c"}


def test_idempotent_call(tmp_path, monkeypatch):
    target = tmp_path / "x" / "y"
    captured = []
    monkeypatch.setattr(sentinel, "register_path", lambda p: captured.append(p))

    # First call: creates x and x/y
    ensure_dirs(target)
    assert set(captured) == {tmp_path / "x", tmp_path / "x" / "y"}

    # Clear captured and call again: nothing new should register
    captured.clear()
    ensure_dirs(target)
    assert captured == []


def test_no_registration_when_exists(tmp_path, monkeypatch):
    # Pre-create nested dirs
    nested = tmp_path / "m" / "n" / "o"
    nested.mkdir(parents=True)

    captured = []
    monkeypatch.setattr(sentinel, "register_path", lambda p: captured.append(p))

    # Should not register anything
    ensure_dirs(nested)
    assert captured == []

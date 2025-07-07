import atexit
from pathlib import Path
from typing import Set

# --- Global registries for cleanup ---
_created_files: Set[Path] = set()
_created_dirs: Set[Path] = set()


def register_path(path: Path) -> None:
    """
    Register a file or directory path for cleanup on program exit.
    Determines automatically whether it's a file or a directory.
    """
    if path.is_dir():
        _created_dirs.add(path)
    else:
        _created_files.add(path)


def cleanup_registered() -> None:
    """
    Delete all registered files and directories at program exit.
    Directories are removed in reverse depth order to ensure they are empty.
    """
    for file in _created_files:
        try:
            if file.exists():
                file.unlink()
        except Exception:
            pass

    for dir_path in sorted(_created_dirs, key=lambda p: len(p.parts), reverse=True):
        try:
            if dir_path.exists():
                dir_path.rmdir()
        except Exception:
            pass


from pathlib import Path
from typing import List

from grpcAPI.files_sentinel import register_path


def ensure_dirs(path: Path) -> None:
    """
    Ensure that `path` exists as a directory (mkdir -p).
    Any directory actually created (i.e. that did not exist before)
    is passed to `register_path`, so it can be cleaned up later.
    """
    to_create: List[Path] = []
    current = path

    # Walk up until we find an existing directory
    while not current.exists():
        to_create.append(current)
        current = current.parent

    # Now create from top-down
    for directory in reversed(to_create):
        directory.mkdir()
        register_path(directory)


atexit.register(cleanup_registered)

import atexit
import logging
from pathlib import Path
from typing import List, Set

logger = logging.getLogger(__name__)

_created_files: Set[Path] = set()
_created_dirs: Set[Path] = set()


def register_path(path: Path) -> None:
    """
    Register a file or directory path for cleanup on program exit.
    Determines automatically whether it's a file or a directory.
    """
    logger.debug(f'Registering: "{path}". Is dir: {path.is_dir()}')
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
        logger.debug(f'File clean up: "{file}". File Exist ?: {file.exists()}')
        try:
            if file.exists():
                file.unlink()
        except Exception:
            pass

    for dir_path in sorted(_created_dirs, key=lambda p: len(p.parts), reverse=True):

        logger.debug(f'Dir clean up: "{dir_path}". Dir Exist ?: {dir_path.exists()}')
        try:
            if dir_path.exists():
                dir_path.rmdir()
        except Exception:
            pass


def ensure_dirs(path: Path, clean: bool = True) -> None:
    """
    Ensure that `path` exists as a directory (mkdir -p).
    If clean flag is true, any directory actually created
    (i.e. that did not exist before) is passed to
    `register_path`, so it can be cleaned up later.
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
        if clean:
            register_path(directory)


atexit.register(cleanup_registered)

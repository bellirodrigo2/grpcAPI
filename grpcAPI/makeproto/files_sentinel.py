import atexit
import logging
import threading
from pathlib import Path
from typing import List, Set

logger = logging.getLogger(__name__)

_created_files: Set[Path] = set()
_created_dirs: Set[Path] = set()


_lock = threading.Lock()


def register_path(path: Path, is_dir: bool) -> None:
    """
    Register a file or directory path for cleanup on program exit.
    """
    if not path:
        raise ValueError("Path cannot be None or empty")

    with _lock:
        resolved_path = path.resolve()
        logger.debug(
            f'Registering: "{resolved_path}". Is dir: arg:"{is_dir}" vs real:"{path.is_dir()}"'
        )
        if is_dir:
            _created_dirs.add(resolved_path)
        else:
            _created_files.add(resolved_path)


def _cleanup_files() -> bool:
    """Clean up registered files. Returns True if interrupted."""
    interrupted = False
    for file in _created_files:
        logger.debug(f'File clean up: "{file}". File Exist ?: {file.exists()}')
        try:
            file.unlink()
        except FileNotFoundError:
            pass  # deleted already
        except OSError as e:
            logger.warning(f"Failed to delete file {file}: {e}")
        except KeyboardInterrupt:
            interrupted = True  # set True and keep cleaning
        except Exception as e:
            logger.error(f"Unexpected error deleting file {file}: {e}")
    return interrupted


def _cleanup_directories() -> bool:
    """Clean up registered directories. Returns True if interrupted."""
    interrupted = False
    # Sort by actual path depth (number of parts), then by string
    for dir_path in sorted(
        _created_dirs, key=lambda p: (len(p.parts), str(p)), reverse=True
    ):
        logger.debug(f'Dir clean up: "{dir_path}". Dir Exist ?: {dir_path.exists()}')
        try:
            if dir_path.is_symlink():
                dir_path.unlink()  # For symlinks
            else:
                dir_path.rmdir()  # For real directories
        except FileNotFoundError:
            pass  # deleted already
        except OSError as e:  # Includes PermissionError and "directory not empty"
            logger.warning(f"Failed to delete directory {dir_path}: {e}")
        except KeyboardInterrupt:
            interrupted = True
        except Exception as e:
            logger.error(f"Unexpected error deleting directory {dir_path}: {e}")
    return interrupted


def cleanup_registered() -> None:
    """
    Delete all registered files and directories at program exit.
    Directories are removed in reverse depth order to ensure they are empty.
    """
    with _lock:
        file_interrupted = _cleanup_files()
        dir_interrupted = _cleanup_directories()

        # Re-raise KeyboardInterrupt at the end if keyboard interrupt
        if file_interrupted or dir_interrupted:
            raise KeyboardInterrupt()


def ensure_dirs(path: Path, clean: bool = True) -> None:
    """
    Ensure that `path` exists as a directory (mkdir -p).
    If clean flag is true, any directory actually created
    (i.e. that did not exist before) is passed to
    `register_path`, so it can be cleaned up later.
    """
    if not path:
        raise ValueError("Path cannot be None or empty")

    to_create: List[Path] = []
    current = path.resolve()

    # Walk up until we find an existing directory
    while not current.exists() and current != current.parent:
        to_create.append(current)
        current = current.parent

    # Now create from top-down and register each created directory
    for directory in reversed(to_create):
        try:
            directory.mkdir()
            if clean:
                register_path(directory, True)
        except OSError as e:
            # If mkdir fails, don't try to create remaining directories
            logger.error(f"Failed to create directory {directory}: {e}")
            break


atexit.register(cleanup_registered)

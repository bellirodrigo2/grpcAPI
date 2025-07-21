import subprocess
from logging import Logger, getLogger
from pathlib import Path
from typing import Optional

from typing_extensions import List

default_logger = getLogger(__name__)


def compile_protoc(
    root: Path,
    dst: Path,
    clss: bool,
    services: bool,
    mypy_stubs: bool,
    files: Optional[List[str]] = None,
    logger: Logger = default_logger,
) -> None:

    if not root.exists():
        raise FileNotFoundError(f"Proto path '{root}' does not exist.")

    if not dst.exists():
        dst.mkdir(parents=True, exist_ok=True)

    if files:
        proto_files = files
    else:
        proto_files = list_proto_files(root)
    if not proto_files:
        raise Exception

    args = [
        "python",
        "-m",
        "grpc_tools.protoc",
        f"-I{str(root)}",
    ]
    if clss:
        args.append(f"--python_out={dst}")
    if services:
        args.append(f"--grpc_python_out={dst}")
    if mypy_stubs:
        args.append(f"--mypy_out={dst}")

    args.extend(proto_files)

    result = subprocess.run(
        args,
        capture_output=True,
        text=True,
    )

    if result.stdout:
        logger.info("protoc stdout:\n%s", result.stdout)

    if result.stderr:
        logger.warning("protoc stderr:\n%s", result.stderr)

    if result.returncode != 0:
        logger.error("protoc failed with exit code %d", result.returncode)
        raise subprocess.CalledProcessError(result.returncode, args)


def list_proto_files(base_dir: Path, rel_path: Optional[Path] = None) -> List[str]:
    base_path = base_dir.resolve()
    rel_path = rel_path or base_path

    return [
        str(path.relative_to(rel_path).as_posix())
        for path in base_path.rglob("*.proto")
    ]


if __name__ == "__main__":
    compile_protoc(
        Path("./tests/proto"),
        Path("./tests/lib"),
        True,
        False,
        True,
    )

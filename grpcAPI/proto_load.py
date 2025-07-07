import importlib.util
import re
from collections import defaultdict
from logging import Logger
from pathlib import Path
from types import ModuleType

from typing_extensions import Dict, Generator, List, Optional, Tuple

from grpcAPI.protoc_compile import compile_protoc

_GRPC_REGEX = re.compile(r"^(?:(.*?)/)?([^/]+)_pb2_grpc\.py$")


def extract_package_module(path: Path, root: Path) -> Optional[Tuple[str, str]]:
    rel_path = path.relative_to(root).as_posix()

    match = _GRPC_REGEX.match(rel_path)
    if not match:
        return None
    package = match.group(1) or ""
    module = match.group(2)
    return package, module


def find_grpc_modules(root_dir: Path) -> Generator[Tuple[str, str, Path]]:

    for path in root_dir.rglob("*_pb2_grpc.py"):
        pack_mod = extract_package_module(path, root_dir)
        if pack_mod is None:
            continue
        package, module = pack_mod
        yield package, module, path


def load_proto(
    root_dir: Path,
    files: List[str],
    dst: Path,
    logger: Logger,
) -> Dict[str, Dict[str, ModuleType]]:

    compile_protoc(
        root=root_dir,
        dst=dst,
        services=True,
        clss=False,
        mypy_stubs=False,
        files=files,
        logger=logger,
    )

    imports: Dict[str, Dict[str, ModuleType]] = defaultdict(dict)

    for package, module, path in find_grpc_modules(dst):
        module_name = (
            f"{package.replace('/', '.')}.{module}_pb2_grpc"
            if package
            else f"{module}_pb2_grpc"
        )
        imported = import_module_from_path(module_name, path)
        imports[package][module] = imported
    return imports


def import_module_from_path(module_name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(module_name, path)
    if not spec or not spec.loader:
        raise ImportError(f"Cannot import {module_name} from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

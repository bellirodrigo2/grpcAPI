import importlib.util
import logging
from collections import defaultdict
from functools import partial
from pathlib import Path
from types import ModuleType
from typing import Callable

from typing_extensions import Dict, List, Tuple, Type

from grpcAPI.config import COMPILE_PROTO, SERVICE_MODULE
from grpcAPI.files_sentinel import register_path
from grpcAPI.interfaces import CompileProto, ServiceModule

logger = logging.getLogger(__name__)


def load_proto_(
    root_dir: Path,
    files: List[str],
    dst: Path,
    module_factory: Type[ServiceModule],
    compile_proto: CompileProto,
    clean_services: bool = True,
) -> Dict[str, Dict[str, ServiceModule]]:

    logger.debug(f'Compiling: "{files}"')
    compile_proto(
        root=root_dir,
        dst=dst,
        services=True,
        clss=False,
        mypy_stubs=False,
        files=files,
        logger=logger,
    )

    imports: Dict[str, Dict[str, ServiceModule]] = defaultdict(dict)
    for file in files:
        package, module = file_package_module(file)
        module_str = module_factory.proto_to_pymodule(file)
        imported = import_file(dst, module_str, clean_services)
        imports[package][module] = module_factory.make(imported)

    return imports


def import_file(root: Path, module_str: str, clean_services: bool) -> ModuleType:
    module_name = module_str.replace("/", ".").strip(".py")
    path = root / module_str

    if clean_services:
        register_path(path)

    return import_module_from_path(module_name, path)


def file_package_module(file: str) -> Tuple[str, str]:
    if "/" in file:
        package, module = file.split("/", 1)
    else:
        package = ""
        module = file
    module = module.replace(".proto", "")
    return package, module


def import_module_from_path(module_name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(module_name, path)
    if not spec or not spec.loader:
        raise ImportError(f"Cannot import {module_name} from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


load_proto = partial(
    load_proto_, module_factory=SERVICE_MODULE, compile_proto=COMPILE_PROTO
)

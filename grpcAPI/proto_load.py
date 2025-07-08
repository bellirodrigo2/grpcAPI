import importlib.util
from collections import defaultdict
from logging import Logger
from pathlib import Path
from types import ModuleType

from typing_extensions import Dict, List, Tuple, Type

from grpcAPI.files_sentinel import register_path
from grpcAPI.interface import IServiceModule
from grpcAPI.protoc_compile import compile_protoc


def load_proto(
    root_dir: Path,
    files: List[str],
    dst: Path,
    logger: Logger,
    module_factory: Type[IServiceModule],
    clean_services: bool = True,
) -> Dict[str, Dict[str, IServiceModule]]:

    compile_protoc(
        root=root_dir,
        dst=dst,
        services=True,
        clss=False,
        mypy_stubs=False,
        files=files,
        logger=logger,
    )

    imports: Dict[str, Dict[str, IServiceModule]] = defaultdict(dict)
    for file in files:
        package, module = file_package_module(file)

        imported = import_file(dst, file, module_factory, clean_services)
        imports[package][module] = imported

    return imports


def import_file(
    root: Path, file: str, module_factory: Type[IServiceModule], clean_services: bool
) -> IServiceModule:

    module_str = module_factory.proto_to_pymodule(file)
    module_name = module_str.replace("/", ".").strip(".py")
    path = root / module_str

    if clean_services:
        register_path(path)

    imported = import_module_from_path(module_name, path)

    return module_factory(imported)


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

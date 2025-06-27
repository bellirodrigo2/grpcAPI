import importlib.util
import sys
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from types import ModuleType
from typing import Any, AsyncGenerator, Dict, List, Union

from grpcAPI.protoc_compiler import compile
from grpcAPI.types.message import NO_PACKAGE


def list_subfolders(path: Union[Path, str]) -> List[Path]:
    path = Path(path)
    return [
        p for p in path.iterdir() if p.is_dir() and not str(p.name).startswith("__")
    ]


def list_proto_files(path: Path) -> list[Path]:
    return [p for p in path.iterdir() if str(p).endswith(".proto")]


def list_compiled_proto_files(path: Path) -> list[Path]:
    def is_module(file: str) -> bool:
        if not file.startswith("__") and file.endswith(".py") and "_pb2" in file:
            print(file)
            return True
        return False

    return [p for p in path.iterdir() if is_module(p.name)]


def import_py_files_from_folder(
    folder: Path, package_prefix: str = ""
) -> Dict[str, ModuleType]:
    modules: Dict[str, ModuleType] = {}

    for py_file in folder.glob("*.py"):
        if py_file.name.startswith("__"):
            continue

        module_name = py_file.stem
        full_module_name = module_name
        if package_prefix:
            full_module_name = f"{package_prefix}.{module_name}"
        spec = importlib.util.spec_from_file_location(full_module_name, py_file)

        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            sys.modules[full_module_name] = module
            spec.loader.exec_module(module)
            normalized_name = module_name.replace("_pb2", "")
            modules[normalized_name] = module

    return modules


def import_modules(
    path: Path, sub_paths: List[str]
) -> Dict[str, Dict[str, ModuleType]]:

    proto_path = path.joinpath(*sub_paths)
    if str(proto_path) not in sys.path:
        sys.path.insert(0, str(proto_path))

    modules: Dict[str, Dict[str, ModuleType]] = {}

    no_pack_module_str = ".".join([path.name, *sub_paths])
    no_package_module: Dict[str, ModuleType] = import_py_files_from_folder(
        proto_path, no_pack_module_str
    )
    modules[NO_PACKAGE] = no_package_module

    packages = list_subfolders(proto_path)
    for pack in packages:
        modules_str = ".".join([path.name, *sub_paths, pack.name])
        module: Dict[str, ModuleType] = import_py_files_from_folder(pack, modules_str)
        modules[pack.name] = module
    return modules


def compile_proto(src_dir: Path, dst_dir: Path) -> None:

    no_packagers = list_proto_files(src_dir)
    for file in no_packagers:
        compile(
            tgt_folder=str(src_dir),
            protofile=file.name,
            output_dir=str(dst_dir),
        )

    packages = list_subfolders(src_dir)
    for package in packages:
        proto_files = list_proto_files(package)
        for file in proto_files:
            tgt_dir = dst_dir / package.name
            tgt_dir.mkdir(exist_ok=True)
            compile(
                tgt_folder=str(src_dir),
                protofile=f"{package.name}/{str(file.name)}",
                output_dir=str(dst_dir),
            )


def load_proto(proto_dir: Path, dst_dir: Path) -> Dict[str, Dict[str, ModuleType]]:
    compile_proto(proto_dir, dst_dir)
    return import_modules(dst_dir.parent, [dst_dir.name])


@contextmanager
def load_proto_temp_lifespan(
    src_path: Path,
) -> AsyncGenerator[Dict[str, Dict[str, ModuleType]], Any]:
    with TemporaryDirectory() as temp_dir:
        output_dir = Path(temp_dir) / "compiled"
        output_dir.mkdir(parents=True, exist_ok=True)

        modules = load_proto(src_path, output_dir)
        yield modules

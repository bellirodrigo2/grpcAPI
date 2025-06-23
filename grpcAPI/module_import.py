import sys
from pathlib import Path
from types import ModuleType
from typing import Dict, List, Union

from grpcAPI.proto_proxy import import_py_files_from_folder


def list_subfolders(path: Union[Path, str]) -> List[Path]:
    path = Path(path)
    return [p for p in path.iterdir() if p.is_dir()]


def import_modules(
    path: Path, sub_paths: List[str]
) -> Dict[str, Dict[str, ModuleType]]:

    proto_path = path.joinpath(*sub_paths)
    if str(proto_path) not in sys.path:
        sys.path.insert(0, str(proto_path))
    packages = list_subfolders(proto_path)
    modules: Dict[str, Dict[str, ModuleType]] = {}
    for pack in packages:
        modules_str = ".".join([path.name, *sub_paths, pack.name])
        module: Dict[str, ModuleType] = import_py_files_from_folder(pack, modules_str)
        modules[pack.name] = module
    return modules


# source_folder = Path(__file__).parent
# p = source_folder / "proto" / "compiled"
# sys.path.append(str(p))

# modules = import_py_files_from_folder(p, f"{source_folder.name}.proto.compiled")
# bind_proto_proxy(user_input, modules)
# bind_proto_proxy(user, modules)
# bind_proto_proxy(user_list, modules)
# bind_proto_proxy(names_id, modules)

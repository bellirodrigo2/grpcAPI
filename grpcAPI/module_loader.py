import os
import sys
from pathlib import Path

from typing_extensions import Any, Dict, List, Optional, Sequence, Tuple, Type

from grpcAPI.app import App
from grpcAPI.interfaces import ServiceModule
from grpcAPI.proto_build import pack_protos
from grpcAPI.proto_load import load_proto
from grpcAPI.singleton import SingletonMeta


def load_app_modules(
    app: App,
    settings: Dict[str, Any],
) -> Dict[str, Dict[str, ServiceModule]]:
    loader = ModuleLoader(app, settings)
    return loader.modules_dict


class ModuleLoader(metaclass=SingletonMeta):
    def __init__(
        self,
        app: App,
        settings: Dict[str, Any],
    ) -> None:
        self.app = app

        proto_path, lib_path = get_proto_lib_path(settings)

        overwrite = False
        clean_services = True

        type_cast = app._validator.casting_list

        pack = pack_protos(
            services=app.services,
            root_dir=proto_path,
            overwrite=overwrite,
            clean_services=clean_services,
            type_cast=type_cast,
        )

        sys.path.insert(0, str(lib_path.resolve()))

        self._modules: Dict[str, Dict[str, ServiceModule]] = load_proto(
            root_dir=proto_path,
            files=list(pack),
            dst=lib_path,
        )

    @property
    def modules_dict(self) -> Dict[str, Dict[str, ServiceModule]]:
        return self._modules


def get_proto_lib_path(
    settings: Dict[str, Any],
) -> Tuple[Path, Path]:
    root_str: Optional[str] = settings.get("root_path", None)
    if not root_str:
        root_str = os.environ.get("PYTHONPATH")
        if not root_str:
            raise RuntimeError
    root_path = Path(root_str)
    proto_str: str = settings.get("proto_rel_path", "proto")
    proto_path = root_path / proto_str
    if not proto_path.exists():
        raise FileNotFoundError

    lib_str: str = settings.get("lib_rel_path", "lib")
    lib_path = root_path / lib_str
    if not lib_path.exists():
        raise FileNotFoundError(str(lib_path.absolute()))
    return proto_path, lib_path

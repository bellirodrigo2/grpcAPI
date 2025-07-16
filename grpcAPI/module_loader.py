import sys
from pathlib import Path

from typing_extensions import Any, Dict, List, Optional, Tuple

from grpcAPI.app import App
from grpcAPI.interfaces import ProcessServiceFactory, ServiceModule
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
        process_service_factory: Optional[List[ProcessServiceFactory]] = None,
    ) -> None:
        self.app = app

        proto_path, lib_path = get_proto_lib_path(settings)

        clean_services, overwrite = get_compile_proto_settings(settings)

        type_cast = app._validator.casting_list

        process_service_factory = process_service_factory or []
        process_service_factory.extend(app._process_service_factories)
        process_services = [
            factory(settings) for factory in set(process_service_factory)
        ]

        pack = pack_protos(
            services=app.services,
            root_dir=proto_path,
            overwrite=overwrite,
            process_services=process_services,
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


def get_compile_proto_settings(
    settings: Dict[str, Any],
) -> Tuple[bool, bool]:
    compile_settings = settings.get("compile_proto", {})
    clean_services = compile_settings.get("clean_services", True)
    ovewrite = compile_settings.get("ovewrite", False)
    return clean_services, ovewrite


def get_proto_lib_path(
    settings: Dict[str, Any],
) -> Tuple[Path, Path]:

    path_settings = settings.get("path", {})

    root_path = Path("./").resolve()

    proto_str: str = path_settings.get("proto_path", "proto")
    proto_path = root_path / proto_str
    if not proto_path.exists():
        raise FileNotFoundError(str(proto_path))

    lib_str: str = path_settings.get("lib_path", "lib")
    lib_path = root_path / lib_str
    if not lib_path.exists():
        raise FileNotFoundError(str(lib_path))
    return proto_path, lib_path

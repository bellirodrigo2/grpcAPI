import itertools
import logging
from pathlib import Path
from typing import Optional, Tuple

from typing_extensions import Any, Dict

from grpcAPI.add_to_server import add_to_server
from grpcAPI.app import App
from grpcAPI.proto_build import make_protos, write_protos
from grpcAPI.protoc_compile import compile_protoc
from grpcAPI.server import make_server
from grpcAPI.server_plugins.loader import get_plugin
from grpcAPI.settings.utils import combine_settings, load_app

logger = logging.getLogger(__name__)


async def run_app(
    app_path: str,
    user_settings: Dict[str, Any],
    host: str,
    port: int,
    lint: Optional[bool] = None,
) -> None:

    load_app(app_path)
    app = App()

    settings = combine_settings(user_settings)

    lint = lint or settings.get("lint", True)
    plugins_settings = settings.get("plugins", {})

    reflection = "reflection" in plugins_settings

    if lint or reflection:
        proto_files = make_protos(app.services, app._casting_list)
        if reflection:
            proto_path, lib_path = get_proto_lib_path(settings)
            clean_services, overwrite = get_compile_proto_settings(settings)
            files = write_protos(proto_files, proto_path, overwrite, clean_services)
            compile_protoc(Path("./"), lib_path, True, False, False, files, logger)

    server_settings = settings.get("server", {})
    middlewares = [middleware() for middleware in set(app._middleware)]

    server = make_server(server_settings, middlewares)

    plugins = [get_plugin(plugin_name) for plugin_name in plugins_settings.keys()]
    for plugin in plugins:
        server.register_plugin(plugin)

    for service in app.service_list:
        add_to_server(
            service, server, app.dependency_overrides, app._exception_handlers
        )
    lifespan = app.lifespan
    server.add_insecure_port(f"{host}:{port}")
    await server.start(lifespan)


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

    root_path = Path("./").resolve()

    proto_str: str = settings.get("proto_path", "proto")
    proto_path = root_path / proto_str
    if not proto_path.exists():
        raise FileNotFoundError(str(proto_path))

    lib_str: str = settings.get("lib_path", "lib")
    lib_path = root_path / lib_str
    if not lib_path.exists():
        raise FileNotFoundError(str(lib_path))
    return proto_path, lib_path

from pathlib import Path
from typing import Optional

from typing_extensions import Any, Dict

from grpcAPI.add_to_server import add_to_server
from grpcAPI.app import App
from grpcAPI.commands.command import GRPCAPICommand
from grpcAPI.commands.process_service.run_process_service import run_process_service
from grpcAPI.commands.settings.utils import combine_settings, load_app
from grpcAPI.commands.utils import (
    get_compile_proto_settings,
    get_host_port,
    get_proto_lib_path,
)
from grpcAPI.makeproto.write_proto import write_protos
from grpcAPI.proto_build import make_protos
from grpcAPI.protoc_compile import compile_protoc
from grpcAPI.server import make_server
from grpcAPI.server_plugins.loader import get_plugin


class RunCommand(GRPCAPICommand):

    def __init__(
        self, command_name: str, app_path: str, settings_path: Optional[str] = None
    ) -> None:
        super().__init__(command_name, app_path, settings_path)

    async def run(self, **kwargs: Any) -> None:

        settings = self.settings
        self.settings.update(kwargs)
        app = self.app

        lint = settings.get("lint", True)
        plugins_settings = settings.get("plugins", {})

        reflection = "reflection" in plugins_settings

        if lint or reflection:
            proto_files = make_protos(app.services)
            self.logger.debug(
                "Generated files:", [(f.package, f.filename) for f in proto_files]
            )
            if reflection:
                proto_path, lib_path = get_proto_lib_path(settings)
                clean_services, overwrite = get_compile_proto_settings(settings)
                files = write_protos(proto_files, proto_path, overwrite, clean_services)
                compile_protoc(
                    Path("./"), lib_path, True, False, False, files, self.logger
                )

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
        host, port = get_host_port(settings)
        server.add_insecure_port(f"{host}:{port}")

        lifespan = app.lifespan
        await server.start(lifespan)


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

    run_process_service(app, settings)

    if lint or reflection:
        proto_files = make_protos(app.services)
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

from contextlib import AsyncExitStack
from typing import Optional

from typing_extensions import Any

from grpcAPI.add_to_server import add_to_server
from grpcAPI.app import App
from grpcAPI.commands.command import GRPCAPICommand
from grpcAPI.commands.utils import get_host_port
from grpcAPI.proto_build import make_protos
from grpcAPI.server import ServerWrapper, make_server
from grpcAPI.server_plugins.loader import make_plugin


class RunCommand(GRPCAPICommand):

    def __init__(self, app: App, settings_path: Optional[str] = None) -> None:
        super().__init__("run", app, settings_path)

    async def run(self, **kwargs: Any) -> None:

        settings = self.settings
        app = self.app

        lint = settings.get("lint", True)
        plugins_settings = settings.get("plugins", {})

        if lint:
            proto_files = make_protos(app.services)
            self.logger.debug(
                "Generated files:", [(f.package, f.filename) for f in proto_files]
            )

        middlewares = [middleware() for middleware in set(app._middleware)]

        if app.server:
            server = ServerWrapper(app.server)
        else:
            server_settings = settings.get("server", {})
            server = make_server(middlewares, **server_settings)

        if "reflection" in plugins_settings:
            pass

        plugins = [
            make_plugin(plugin_name, **kwargs)
            for plugin_name, kwargs in plugins_settings.items()
        ]
        for plugin in plugins:
            server.register_plugin(plugin)

        for service in app.service_list:
            if service.active:
                add_to_server(
                    service, server, app.dependency_overrides, app._exception_handlers
                )
        host, port = get_host_port(settings)
        server.add_insecure_port(f"{host}:{port}")

        async with AsyncExitStack() as stack:
            for lifespan in app.lifespan:
                await stack.enter_async_context(lifespan(app))
            await server.start()
            await server.wait_for_termination()

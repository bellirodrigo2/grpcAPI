from contextlib import AsyncExitStack

from typing_extensions import Any, Optional

from grpcAPI.add_to_server import add_to_server
from grpcAPI.app import App
from grpcAPI.build_proto import make_protos
from grpcAPI.commands.command import GRPCAPICommand

# from grpcAPI.commands.utils import get_host_port
from grpcAPI.load_credential import get_server_certificate
from grpcAPI.server import ServerWrapper, make_server
from grpcAPI.server_plugins.loader import make_plugin


class RunCommand(GRPCAPICommand):

    def __init__(self, app: App, settings_path: Optional[str] = None) -> None:
        super().__init__("run", app, settings_path)

    async def run(self, **kwargs: Any) -> None:

        settings = self.settings
        app = self.app
        lint = kwargs.get("lint") or settings.get("lint", True)
        plugins_settings = settings.get("plugins", {})

        if lint:
            proto_files = make_protos(app.services)
            self.logger.debug(
                "Generated files:", [(f.package, f.filename) for f in proto_files]
            )

        if app.server:
            server = ServerWrapper(app.server)
        else:
            server_settings = settings.get("server", {})
            server = make_server(app.interceptors, **server_settings)

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
        host = kwargs.get("host") or settings.get("host", "localhost")
        port = kwargs.get("port") or settings.get("port", 50051)
        port = int(port)
        tls = settings.get("tls", {"enabled": False})
        if tls.get("enabled"):
            credential = get_server_certificate(
                tls.get("certificate"),
                tls.get("key"),
            )
            server.add_secure_port(f"{host}:{port}", credential)
        else:
            server.add_insecure_port(f"{host}:{port}")

        async with AsyncExitStack() as stack:
            for lifespan in app.lifespan:
                await stack.enter_async_context(lifespan(app))
            await server.start()
            await server.wait_for_termination()

from functools import partial

from typing_extensions import Any, Dict

from grpcAPI.add_to_server import add_to_server
from grpcAPI.app import App
from grpcAPI.config import SERVER_FACTORY
from grpcAPI.interfaces import SeverFactory
from grpcAPI.module_loader import load_app_modules
from grpcAPI.server_plugins.factory import get_plugin
from grpcAPI.server_plugins.plugins import reflection
from grpcAPI.service_provider import provide_services
from grpcAPI.settings.utils import combine_settings, load_app


async def run_app_(
    app_path: str,
    user_settings: Dict[str, Any],
    host: str,
    port: int,
    server_factory: SeverFactory,
) -> None:

    load_app(app_path)
    app = App()

    settings = combine_settings(user_settings)

    server_settings = settings.get("server", {})
    middlewares = [middleware() for middleware in set(app._middleware)]

    lint = True
    reflection = "reflection" in server_settings.get("plugins", {})

    # if reflection_plugin...should compile service .proto files for python_out only
    if lint or reflection:
        # makeproto compile_service
        if reflection:
            # write to the same dir package/module.proto
            # track to delete on atexit, package dir if not exist before, and .proto
            proto_path = settings.get("proto_path", "proto")
            # protoc compile python_out the service .protos on tempdir
            pass
        pass

    server = make_server(server_settings, middlewares)

    services = [item for sublist in app.services.values() for item in sublist]

    for service in services:
        add_to_server(
            service, server, app.dependency_overrides, app._exception_handlers
        )

    await server.start(host, port, None)

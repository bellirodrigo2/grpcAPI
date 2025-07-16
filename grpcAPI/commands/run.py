from functools import partial

from typing_extensions import Any, Dict

from grpcAPI.app import App
from grpcAPI.config import SERVER_FACTORY
from grpcAPI.interfaces import SeverFactory
from grpcAPI.module_loader import load_app_modules
from grpcAPI.plugins.factory import get_plugin
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

    modules_dict = load_app_modules(app, settings)

    server_settings = settings.get("server", {})
    plugins_config = server_settings.get("plugins", {})
    plugins = [get_plugin(plugin_name) for plugin_name in plugins_config]

    middlewares = [middleware() for middleware in set(app._middleware)]

    server = server_factory(
        options=[],
        plugins=plugins,
        middlewares=middlewares,
        settings=settings,
    )
    for plugin in plugins:
        name = plugin.plugin_name
        plugin.configure(server, plugins_config[name])

    services = [item for sublist in app.services.values() for item in sublist]
    for service_cls in provide_services(
        services=services,
        modules=modules_dict,
        overrides=app.dependency_overrides,
        exception_registry=app._exception_handlers,
    ):
        server.add_service(service_cls)

    await server.start(host, port, None)


run_app = partial(run_app_, server_factory=SERVER_FACTORY)

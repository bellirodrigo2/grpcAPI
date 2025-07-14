import asyncio
from collections.abc import AsyncIterator
from functools import partial

from typing_extensions import Any, Dict

from grpcAPI.app import App
from grpcAPI.config import SERVER_FACTORY
from grpcAPI.grpcapi import GrpcAPI
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

    server = server_factory(
        options=[],
        plugins=plugins,
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

if __name__ == "__main__":
    from google.protobuf.descriptor_pb2 import DescriptorProto
    from google.protobuf.timestamp_pb2 import Timestamp

    from grpcAPI.app import APIService
    from grpcAPI.lib.other_pb2 import Other
    from grpcAPI.lib.user_pb2 import User

    serviceapi2 = APIService(
        name="service2",
    )

    @serviceapi2
    async def unary(req: User) -> DescriptorProto:
        return DescriptorProto()

    @serviceapi2
    async def clientstream(req: AsyncIterator[DescriptorProto]) -> Other:
        return Other()

    class AsyncUserIterator:
        def __init__(self) -> None:
            self._data = [User(), User()]
            self._index = 0

        def __aiter__(self):
            return self

        async def __anext__(self) -> User:
            if self._index >= len(self._data):
                raise StopAsyncIteration
            value = self._data[self._index]
            self._index += 1
            return value

    class AsyncTimeIterator:
        def __init__(self) -> None:
            self._data = [Timestamp(), Timestamp()]
            self._index = 0

        def __aiter__(self):
            return self

        async def __anext__(self) -> User:
            if self._index >= len(self._data):
                raise StopAsyncIteration
            value = self._data[self._index]
            self._index += 1
            return value

    @serviceapi2
    async def serverstream(req: Other) -> AsyncIterator[Timestamp]:
        it = AsyncTimeIterator()
        async for u in it:
            yield u

    @serviceapi2
    async def bilateral(req: AsyncIterator[Timestamp]) -> AsyncIterator[User]:
        it = AsyncUserIterator()
        async for u in it:
            yield u

    app = GrpcAPI()
    app.add_service(serviceapi2)
    asyncio.run(run_app("./grpcAPI/funclabel.py", {}, "0.0.0.0", 50051))

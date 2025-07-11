import asyncio
import os
import sys
from collections.abc import AsyncIterator
from logging import getLogger
from pathlib import Path

from typing_extensions import Any, Dict, List, Optional, Type

from grpcAPI.app import App
from grpcAPI.grpcio_adaptor.async_server import GRPCAIOServer
from grpcAPI.grpcio_adaptor.extract_types import extract_request_response_type
from grpcAPI.grpcio_adaptor.imodule import GrpcioServiceModule
from grpcAPI.grpcio_adaptor.make_method import make_method_async
from grpcAPI.grpcio_adaptor.makeproto_pass import validate_signature_pass
from grpcAPI.grpcio_adaptor.server_plugins.health_check import HealthCheckPlugin
from grpcAPI.grpcio_adaptor.server_plugins.reflection import ReflectionPlugin
from grpcAPI.proto_build import pack_protos
from grpcAPI.proto_load import load_proto
from grpcAPI.service_provider import provide_service
from grpcAPI.settings.utils import combine_settings, load_app


async def run_app(
    app_path: str,
    user_settings: Dict[str, Any],
    host: str,
    port: int,
) -> None:

    load_app(app_path)
    app = App()

    settings = combine_settings(user_settings)

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

    overwrite = False
    clean_services = True

    pack = pack_protos(
        services=app.services,
        root_dir=proto_path,
        custompassmethod=validate_signature_pass,
        overwrite=overwrite,
        clean_services=clean_services,
    )
    default_logger = getLogger(__name__)

    sys.path.insert(0, str(lib_path.resolve()))

    modules_dict = load_proto(
        root_dir=proto_path,
        files=list(pack),
        dst=lib_path,
        logger=default_logger,
        module_factory=GrpcioServiceModule,
    )
    service_classes: List[Type[Any]] = []
    for services in app.services.values():
        for service in services:
            module_package = modules_dict.get(service.package, {})
            for service_module in module_package.values():
                service_class = provide_service(
                    service=service,
                    module=service_module,
                    make_method=make_method_async,
                    overrides=app.dependency_overrides,
                    exception_registry=app._exception_handlers,
                )
                service_classes.append(service_class)
    server_settings = settings.get("server", None)
    plugins_config = server_settings.get("plugins", None)
    if plugins_config:
        plugins = []
        # create plugins and configure
    else:
        plugins = []

    server = GRPCAIOServer(
        options=[],
        plugins=[HealthCheckPlugin(), ReflectionPlugin()],
        settings=settings,
    )
    for service_cls in service_classes:
        server.add_service(service_cls)
    await server.start(host, port)


if __name__ == "__main__":
    from google.protobuf.descriptor_pb2 import DescriptorProto
    from google.protobuf.timestamp_pb2 import Timestamp

    from grpcAPI.app import BaseService
    from grpcAPI.lib.other_pb2 import Other
    from grpcAPI.lib.user_pb2 import User

    serviceapi2 = BaseService(
        name="service2", extract_metatypes=extract_request_response_type
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

    app = App()
    app.add_service(serviceapi2)
    asyncio.run(run_app("./grpcAPI/funclabel.py", {}, "0.0.0.0", 50051))

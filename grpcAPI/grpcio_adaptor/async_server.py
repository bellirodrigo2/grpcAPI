import logging

import grpc
from typing_extensions import (
    Any,
    AsyncGenerator,
    Callable,
    Dict,
    List,
    Optional,
    Tuple,
    Type,
)

from grpcAPI.grpcio_adaptor.interceptor import AioInterceptor
from grpcAPI.interfaces import ServerContext, ServerPlugin, ServiceModule

logger = logging.getLogger("grpcAPI.server")


class GRPCAIOServer(ServerContext):
    def __init__(
        self,
        options: Optional[List[Tuple[str, Any]]] = None,
        middlewares: Optional[List[AioInterceptor]] = None,
        plugins: Optional[List[ServerPlugin]] = None,
        settings: Optional[Dict[str, Any]] = None,
        block_wait: bool = True,
    ) -> None:
        options = options or []
        middlewares = middlewares or []
        self._grpc_server = grpc.aio.server(options=options, interceptors=middlewares)
        self._plugins = plugins or []
        self._settings = settings or {}
        self._block_wait = block_wait

        for plugin in self._plugins:
            plugin.configure(self, self._settings)

    @property
    def grpc_server(self) -> grpc.aio.Server:
        return self._grpc_server

    def register_service_event(self, service_name: str) -> None:
        for plugin in self._plugins:
            plugin.on_add_service(service_name)

    def add_service(self, service: Type[Any]) -> None:
        instance = service()
        service_grpc: ServiceModule = instance._get_module()
        add_server = service_grpc.get_add_server(service.__name__)
        add_server(instance, self._grpc_server)

        self.register_service_event(service.__name__)

    async def _start(self) -> None:
        for plugin in self._plugins:
            plugin.on_start()

        await self._grpc_server.start()
        logger.info("Server started:")
        if self._block_wait:
            await self._grpc_server.wait_for_termination()

    async def start(
        self,
        host: str = "0.0.0.0",
        port: int = 50051,
        lifespan: Optional[
            Callable[[ServerContext], AsyncGenerator[None, None]]
        ] = None,
    ) -> None:
        self._grpc_server.add_insecure_port(f"{host}:{port}")
        logger.info(f"Starting server at: host: {host}, port: {port}")

        if lifespan:
            async with lifespan(self):
                await self._start()
        else:
            await self._start()


def grpcaio_server_factory(
    options: List[Tuple[str, Any]],
    plugins: Optional[List["ServerPlugin"]] = None,
    settings: Optional[Dict[str, Any]] = None,
    block_wait: bool = True,
) -> ServerContext:
    return GRPCAIOServer(
        options=options, plugins=plugins, settings=settings, block_wait=block_wait
    )

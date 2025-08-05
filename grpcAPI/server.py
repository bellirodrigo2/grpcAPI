from typing import Any, AsyncGenerator, Callable, Dict, Mapping

import grpc
from typing_extensions import Any, List, Optional, Protocol, Sequence

from grpcAPI.app import Middleware


class ServerPlugin(Protocol):

    @property
    def state(self) -> Mapping[str, Any]:
        """Return plugin state information."""
        ...

    def on_register(self, server: "ServerWrapper") -> None:
        """Called when plugin is registered with server."""
        pass

    def on_add_service(self, service_name: str, server: "ServerWrapper") -> None:
        """Called when a service is added to the server."""
        pass

    async def on_start(self) -> None:
        """Called when server is starting."""
        pass

    async def on_stop(self) -> None:
        """Called when server is stopping."""
        pass


class ServerWrapper:

    def __init__(
        self, server: grpc.aio.Server, plugins: Optional[List[ServerPlugin]] = None
    ) -> None:
        self._server: grpc.aio.Server = server
        self.plugins = plugins or []

    @property
    def server(self) -> grpc.aio.Server:
        return self._server

    def register_plugin(self, plugin: ServerPlugin) -> None:
        plugin.on_register(self)
        self.plugins.append(plugin)

    def add_generic_rpc_handlers(
        self, generic_rpc_handlers: Sequence[grpc.GenericRpcHandler]
    ) -> None:
        if generic_rpc_handlers:
            for handler in generic_rpc_handlers:
                service_name = getattr(handler, "_name", "unknown_service")
                for plugin in self.plugins:
                    plugin.on_add_service(service_name, self)
        return self._server.add_generic_rpc_handlers(generic_rpc_handlers)
        # for plugin in self.plugins:
        #     plugin.on_add_service(generic_rpc_handlers[0]._name, self._server)
        # return self._server.add_generic_rpc_handlers(generic_rpc_handlers)

    def add_insecure_port(self, address: str) -> int:
        return self._server.add_insecure_port(address)

    def add_secure_port(
        self, address: str, server_credentials: grpc.ServerCredentials
    ) -> int:
        return self._server.add_secure_port(address, server_credentials)

    async def start(
        self,
        lifespan: Optional[
            Callable[["ServerWrapper"], AsyncGenerator[None, None]]
        ] = None,
    ) -> None:
        for plugin in self.plugins:
            if hasattr(plugin, "on_start"):
                await plugin.on_start()
        # if lifespan:
        #     async with lifespan(self):
        #         await self._server.start()
        # else:
        #     await self._server.start()

        if lifespan:
            lifespan_gen = lifespan(self)
            try:
                await lifespan_gen.__anext__()
                await self._server.start()
            except StopAsyncIteration:
                await self._server.start()
            finally:
                try:
                    await lifespan_gen.__anext__()
                except StopAsyncIteration:
                    pass
        else:
            await self._server.start()

    async def stop(self, grace: Optional[float]) -> None:

        for plugin in self.plugins:
            if hasattr(plugin, "on_stop"):
                await plugin.on_stop()
        return await self._server.stop(grace)

    async def wait_for_termination(self, timeout: Optional[float] = None) -> bool:
        return await self._server.wait_for_termination(timeout)

    def add_registered_method_handlers(
        self, service_name: str, method_handlers: Any
    ) -> None:
        self.server.add_registered_method_handlers(service_name, method_handlers)


def make_server(
    server_settings: Dict[str, Any],
    middlewares: Optional[List[Middleware]],
    # migration_thread_pool: Optional[Executor] = None,
    # maximum_concurrent_rpcs: Optional[int] = None,
    # compression: Optional[grpc.Compression] = None,
) -> ServerWrapper:
    options = server_settings.items()
    server = grpc.aio.server(interceptors=middlewares, options=options)
    return ServerWrapper(server, [])

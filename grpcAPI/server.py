import grpc
from typing_extensions import (
    Any,
    Dict,
    Iterable,
    List,
    Mapping,
    Optional,
    Protocol,
    Sequence,
    Tuple,
)


class ServerPlugin(Protocol):

    @property
    def plugin_name(self) -> str:
        """Return the name of the plugin."""
        ...

    @property
    def state(self) -> Mapping[str, Any]:
        """Return plugin state information."""
        ...

    def on_register(self, server: "ServerWrapper") -> None:
        """Called when plugin is registered with server."""
        pass

    def on_add_service(
        self, service_name: str, methods_name: Iterable[str], server: "ServerWrapper"
    ) -> None:
        """Called when a service is added to the server."""
        pass

    def on_add_port(
        self, address: str, credentials: Optional[grpc.ServerCredentials]
    ) -> None:
        pass

    async def on_start(self, server: "ServerWrapper") -> None:
        """Called when server is starting."""
        pass

    async def on_wait_for_termination(self, timeout: Optional[float] = None) -> None:
        """Called when server is waiting for termination."""
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

    def _trigger_plugins(self, trigger: str, **kwargs: Any) -> None:
        for plugin in self.plugins:
            func = getattr(plugin, trigger, None)
            if func:
                func(**kwargs)

    async def _trigger_plugins_async(self, trigger: str, **kwargs: Any) -> None:
        for plugin in self.plugins:
            func = getattr(plugin, trigger, None)
            if func:
                await func(**kwargs)

    def register_plugin(self, plugin: ServerPlugin) -> None:
        plugin.on_register(self)
        self.plugins.append(plugin)

    def add_generic_rpc_handlers(
        self, generic_rpc_handlers: Sequence[grpc.GenericRpcHandler]
    ) -> None:
        return self._server.add_generic_rpc_handlers(generic_rpc_handlers)

    def add_registered_method_handlers(
        self, service_name: str, method_handlers: Dict[str, Any]
    ) -> None:
        self._trigger_plugins(
            "on_add_service",
            service_name=service_name,
            methods_name=method_handlers.keys(),
            server=self,
        )
        self.server.add_registered_method_handlers(service_name, method_handlers)

    def add_insecure_port(self, address: str) -> int:
        self._trigger_plugins("on_add_port", address=address, credentials=None)
        return self._server.add_insecure_port(address)

    def add_secure_port(
        self, address: str, server_credentials: grpc.ServerCredentials
    ) -> int:
        self._trigger_plugins(
            "on_add_port", address=address, credentials=server_credentials
        )
        return self._server.add_secure_port(address, server_credentials)

    async def start(
        self,
    ) -> None:
        await self._trigger_plugins_async("on_start", server=self)
        await self._server.start()

    async def stop(self, grace: Optional[float]) -> None:
        await self._trigger_plugins_async("on_stop")
        return await self._server.stop(grace)

    async def wait_for_termination(self, timeout: Optional[float] = None) -> bool:
        await self._trigger_plugins_async("on_wait_for_termination", timeout=timeout)
        return await self._server.wait_for_termination(timeout)


_compression_map = {
    "gzip": grpc.Compression.Gzip,
    "deflate": grpc.Compression.Deflate,
    "none": grpc.Compression.NoCompression,
}


def make_server(
    interceptors: Optional[List[grpc.aio.ServerInterceptor]], **server_settings: Any
) -> ServerWrapper:
    options: Sequence[Tuple[str, Any]] = server_settings.get("options", [])
    maximum_concurrent_rpcs = server_settings.get("maximum_concurrent_rpcs")
    compression = server_settings.get("compression", "none")
    server = grpc.aio.server(
        interceptors=interceptors,
        maximum_concurrent_rpcs=maximum_concurrent_rpcs,
        compression=_compression_map.get(compression, grpc.Compression.NoCompression),
        options=options,
    )
    return ServerWrapper(server, [])

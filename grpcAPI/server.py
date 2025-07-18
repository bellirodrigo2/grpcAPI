import grpc
from typing_extensions import List, Optional, Protocol, Sequence


class ServerPlugin(Protocol):

    def on_add_service(self, service_name: str, server: "ServerWrapper") -> None:
        pass

    def on_start(self) -> None:
        pass

    def on_stop(self) -> None:
        pass


class ServerWrapper:

    def __init__(
        self, server: grpc.aio.Server, plugins: Optional[List[ServerPlugin]] = None
    ) -> None:
        self._server = server
        self.plugins = plugins or []

    def register_plugin(self, plugin: ServerPlugin) -> None:
        self.plugins.append(plugin)

    def add_generic_rpc_handlers(
        self, generic_rpc_handlers: Sequence[grpc.GenericRpcHandler]
    ) -> None:
        for plugin in self.plugins:
            plugin.on_add_service(generic_rpc_handlers[0]._name, self._server)
        return self._server.add_generic_rpc_handlers(generic_rpc_handlers)

    def add_insecure_port(self, address: str) -> int:
        return self._server.add_insecure_port(address)

    def add_secure_port(
        self, address: str, server_credentials: grpc.ServerCredentials
    ) -> int:
        return self._server.add_secure_port(address, server_credentials)

    async def start(self) -> None:
        return await self._server.start()

    async def stop(self, grace: Optional[float]) -> None:
        return await self._server.stop(grace)

    async def wait_for_termination(self, timeout: Optional[float] = None) -> bool:
        return await self._server.wait_for_termination(timeout)

    def add_registered_method_handlers(self, service_name, method_handlers) -> None:
        return self._server.add_registered_method_handlers(
            service_name, method_handlers
        )

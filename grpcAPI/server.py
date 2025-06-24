from types import ModuleType
from typing import Any, AsyncGenerator, Callable, Dict, Optional, Protocol, Type

import grpc


class IServer(Protocol):

    def add_service(self, service: Type[Any]) -> None: ...

    async def start(self, port: str) -> None: ...


class Server(IServer):

    def __init__(self, modules: Dict[str, Dict[str, ModuleType]]) -> None:
        self.server = grpc.aio.server()
        self.modules = modules

    def add_service(self, service: Type[Any]) -> None:
        instance = service()
        package, module = instance.label
        service_grpc = self.modules[package][f"{module}_grpc"]
        add_server = getattr(service_grpc, f"add_{service.__name__}Servicer_to_server")
        add_server(instance, self.server)

    async def _start(self) -> None:
        await self.server.start()
        print("Server started on :50051")
        await self.server.wait_for_termination()

    async def start(
        self,
        port: str = "[::]:50051",
        lifespan: Optional[Callable[["Server"], AsyncGenerator[None, None]]] = None,
    ) -> None:
        self.server.add_insecure_port(port)
        if lifespan is None:
            await self._start()
        else:
            async with lifespan(self):
                await self._start()

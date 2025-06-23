from types import ModuleType
from typing import Any, Dict, Protocol

import grpc


class IServer(Protocol):

    def add_service(self, service: type[Any]) -> None: ...

    async def start(self, port: str) -> None: ...


class Server(IServer):

    def __init__(self, modules: Dict[str, Dict[str, ModuleType]]) -> None:
        self.server = grpc.aio.server()
        self.modules = modules

    def add_service(self, service: type[Any]) -> None:
        instance = service()
        package, module = instance.label
        service_grpc = self.modules[package][f"{module}_grpc"]
        add_server = getattr(service_grpc, f"add_{service.__name__}Servicer_to_server")
        add_server(instance, self.server)

    async def start(self, port: str = "[::]:50051") -> None:
        self.server.add_insecure_port(port)
        await self.server.start()
        print("Server started on :50051")
        await self.server.wait_for_termination()

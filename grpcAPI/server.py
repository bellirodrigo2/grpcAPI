from types import ModuleType
from typing import (
    Any,
    AsyncGenerator,
    Callable,
    Dict,
    List,
    Optional,
    Protocol,
    Tuple,
    Type,
)

import grpc
from grpc_health.v1 import health, health_pb2, health_pb2_grpc
from grpc_reflection.v1alpha import reflection


class IServer(Protocol):

    def add_service(self, service: Type[Any]) -> None: ...

    async def start(
        self,
        host: str = "0.0.0.0",
        port: int = 50051,
        lifespan: Optional[Callable[["Server"], AsyncGenerator[None, None]]] = None,
    ) -> None: ...


class Server(IServer):

    def __init__(
        self,
        modules: Dict[str, Dict[str, ModuleType]],
        options: List[Tuple[str, Any]],
        health_check: bool,
        reflection: bool,
        block_wait: bool,
    ) -> None:
        self.server = grpc.aio.server(options=options)
        self.block_wait = block_wait
        self.modules = modules

        self.reflection = reflection
        self.services_to_reflect = []

        self.health_check = health_check
        if health_check:
            self.health_servicer = health.HealthServicer()
            health_pb2_grpc.add_HealthServicer_to_server(
                self.health_servicer, self.server
            )

    def add_service(self, service: Type[Any]) -> None:
        instance = service()
        package, module = instance.label
        service_grpc = self.modules[package][f"{module}_grpc"]
        add_server = getattr(service_grpc, f"add_{service.__name__}Servicer_to_server")
        add_server(instance, self.server)

        if hasattr(self, "health_servicer"):
            self.health_servicer.set(
                service.__name__, health_pb2.HealthCheckResponse.SERVING
            )
        self.services_to_reflect.append(service.__name__)

    async def _start(self) -> None:

        if self.reflection:
            services = self.services_to_reflect + [
                reflection.SERVICE_NAME,
                "grpc.health.v1.Health",  # Add health if enabled
            ]
            reflection.enable_server_reflection(services, self.server)

        await self.server.start()
        print("Server started on :50051")
        if self.block_wait:
            await self.server.wait_for_termination()

    async def start(
        self,
        host: str = "0.0.0.0",
        port: int = 50051,
        lifespan: Optional[Callable[["Server"], AsyncGenerator[None, None]]] = None,
    ) -> None:
        bind_address = f"{host}:{port}"
        self.server.add_insecure_port(bind_address)
        if lifespan is None:
            await self._start()
        else:
            async with lifespan(self):
                await self._start()

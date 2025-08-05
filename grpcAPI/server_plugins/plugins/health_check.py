import asyncio
from typing import Optional

from grpc_health.v1 import health, health_pb2, health_pb2_grpc
from typing_extensions import Any, Mapping, Set

from grpcAPI.server import ServerPlugin, ServerWrapper
from grpcAPI.server_plugins import loader


class HealthCheckPlugin(ServerPlugin):
    def __init__(self, grace: Optional[float] = 2.0) -> None:
        self.plugin_name = "health_check"
        self._servicer: health.HealthServicer = health.HealthServicer()
        self._services_set: Set[str] = set()
        self.grace = grace

    @property
    def state(self) -> Mapping[str, Any]:
        return {
            "name": self.plugin_name,
            "servicer": self._servicer,
            "services": list(self._services_set),
            "grace": self.grace,
        }

    def on_register(self, server: ServerWrapper) -> None:
        health_pb2_grpc.add_HealthServicer_to_server(self._servicer, server.server)
        self._servicer.set("", health_pb2.HealthCheckResponse.SERVING)
        self._services_set.add("")

    def on_add_service(self, service_name: str, server: Any) -> None:
        self._servicer.set(service_name, health_pb2.HealthCheckResponse.SERVING)
        self._services_set.add(service_name)

    async def on_stop(self) -> None:
        for service_name in self._services_set:
            self._servicer.set(service_name, health_pb2.HealthCheckResponse.NOT_SERVING)
        if self.grace is not None:
            await asyncio.sleep(self.grace)


def register() -> None:
    loader.register("health_check", HealthCheckPlugin)

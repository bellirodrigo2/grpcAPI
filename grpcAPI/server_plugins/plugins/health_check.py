import asyncio
from typing import Dict, Optional

from grpc_health.v1 import health, health_pb2, health_pb2_grpc
from typing_extensions import Any, Mapping, Set

from grpcAPI.server_plugins import ServerPlugin, loader


class HealthCheckPlugin(ServerPlugin):
    def __init__(self, grace: Optional[float] = 2.0) -> None:
        self.plugin_name = "health_check"
        self._servicer: health.HealthServicer = health.HealthServicer()
        self._services_set: Set[str] = set()
        self.grace = grace

    @property
    def state(self) -> Dict[str, Any]:
        return {
            "name": self.plugin_name,
            "servicer": self._servicer,
            "services": list(self._services_set),
            "grace": self.grace,
        }

    def configure(self, context: ServerContext, settings: Mapping[str, Any]) -> None:
        health_pb2_grpc.add_HealthServicer_to_server(
            self._servicer, context.grpc_server
        )
        self._servicer.set("", health_pb2.HealthCheckResponse.SERVING)
        self._services_set.add("")

    def on_add_service(self, service_name: str) -> None:
        self._servicer.set(service_name, health_pb2.HealthCheckResponse.SERVING)
        self._services_set.add(service_name)

    def on_start(self) -> None:
        return

    def on_stop(self) -> None:
        for service_name in self._services_set:
            self._servicer.set(service_name, health_pb2.HealthCheckResponse.NOT_SERVING)
        asyncio.sleep(self.grace)


def register() -> None:
    loader.register("health_check", HealthCheckPlugin)

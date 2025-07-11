from grpc_health.v1 import health, health_pb2, health_pb2_grpc
from typing_extensions import Any, Dict, Optional

from grpcAPI.server import IServerContext, IServerPlugin


class HealthCheckPlugin(IServerPlugin):
    def __init__(self) -> None:
        self._enabled = False
        self._servicer: Optional[health.HealthServicer] = None

    def configure(self, context: IServerContext, settings: Dict[str, Any]) -> None:
        self._enabled = settings.get("health_check", True)
        if self._enabled:
            self._servicer = health.HealthServicer()
            health_pb2_grpc.add_HealthServicer_to_server(
                self._servicer, context.grpc_server
            )

    def on_add_service(self, service_name: str) -> None:
        if self._enabled and self._servicer:
            self._servicer.set(service_name, health_pb2.HealthCheckResponse.SERVING)

    def on_start(self) -> None:
        return

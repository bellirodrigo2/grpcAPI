from grpc_reflection.v1alpha import reflection
from typing_extensions import Any, Dict, Optional

from grpcAPI.server import IServerContext, IServerPlugin


class ReflectionPlugin(IServerPlugin):
    def __init__(self) -> None:
        self._enabled = False
        self._context: Optional[IServerContext] = None
        self._services: list[str] = []

    def configure(self, context: IServerContext, settings: Dict[str, Any]) -> None:
        self._enabled = settings.get("reflection", True)
        self._context = context

    def on_add_service(self, service_name: str) -> None:
        if self._enabled:
            self._services.append(service_name)

    def on_start(self) -> None:
        if self._enabled and self._context:
            services = self._services + [
                reflection.SERVICE_NAME,
                "grpc.health.v1.Health",
            ]
            reflection.enable_server_reflection(services, self._context.grpc_server)

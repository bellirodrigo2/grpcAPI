from grpc_reflection.v1alpha import reflection
from typing_extensions import Any, Mapping, Optional

from grpcAPI.interfaces import ServerContext, ServerPlugin
from grpcAPI.plugins import factory


class ReflectionPlugin(ServerPlugin):
    def __init__(self) -> None:
        self._enabled = False
        self.plugin_name = "reflection"
        self._context: Optional[ServerContext] = None
        self._services: list[str] = []

    def configure(self, context: ServerContext, settings: Mapping[str, Any]) -> None:
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


def register() -> None:
    factory.register("reflection", ReflectionPlugin)

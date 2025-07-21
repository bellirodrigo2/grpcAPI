from grpc_reflection.v1alpha import reflection
from typing_extensions import Any, Mapping, Optional

from grpcAPI.process_service import ServerContext, ServerPlugin
from grpcAPI.server_plugins import loader


class ReflectionPlugin(ServerPlugin):
    def __init__(self) -> None:
        self.plugin_name = "reflection"
        self._context: Optional[ServerContext] = None
        self._services: list[str] = []

    def configure(self, context: ServerContext, settings: Mapping[str, Any]) -> None:
        self._context = context

    def on_add_service(self, service_name: str) -> None:
        reflection.enable_server_reflection(service_name, self._context.grpc_server)

    def on_start(self) -> None:
        return

    def on_stop(self) -> None:
        return


def register() -> None:
    loader.register("reflection", ReflectionPlugin)

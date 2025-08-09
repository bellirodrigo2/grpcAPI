from collections.abc import Iterable

from grpc_reflection.v1alpha import reflection
from typing_extensions import Any, Mapping, Set

from grpcAPI.server import ServerPlugin, ServerWrapper
from grpcAPI.server_plugins import loader


class ReflectionPlugin(ServerPlugin):
    def __init__(self) -> None:
        self._services: Set[str] = set()

    @property
    def plugin_name(self) -> str:
        return "reflection"

    @property
    def state(self) -> Mapping[str, Any]:
        return {
            "name": self.plugin_name,
            "services": list(self._services),
        }

    def on_add_service(
        self, service_name: str, methods_name: Iterable[str], server: "ServerWrapper"
    ) -> None:
        service_names = (service_name,)
        reflection.enable_server_reflection(service_names, server.server)
        self._services.add(service_name)


def register() -> None:
    loader.register("reflection", ReflectionPlugin)

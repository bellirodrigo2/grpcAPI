from collections.abc import Iterable

from grpc_reflection.v1alpha import reflection
from typing_extensions import Any, Mapping, Set

from grpcAPI.server import ServerPlugin, ServerWrapper
from grpcAPI.server_plugins import loader


class ReflectionPlugin(ServerPlugin):
    def __init__(self) -> None:
        self._services: Set[str] = set()
        # self._services.add(reflection.SERVICE_NAME)

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
        self._services.add(service_name)

    async def on_start(self, server: "ServerWrapper") -> None:
        reflection.enable_server_reflection(self._services, server.server)


def register() -> None:
    loader.register("reflection", ReflectionPlugin)

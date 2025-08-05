from typing import Any, List, Mapping

from grpcAPI.server import ServerPlugin, ServerWrapper


class MockPlugin(ServerPlugin):
    def __init__(self, name: str = "mock_plugin"):
        self.plugin_name = name
        self.on_register_called = False
        self.on_add_service_called = False
        self.on_stop_called = False
        self.services: List[str] = []

    @property
    def state(self) -> Mapping[str, Any]:
        return {
            "name": self.plugin_name,
            "services": self.services,
            "on_register_called": self.on_register_called,
            "on_add_service_called": self.on_add_service_called,
            "on_stop_called": self.on_stop_called,
        }

    def on_register(self, server: ServerWrapper) -> None:
        self.on_register_called = True

    def on_add_service(self, service_name: str, server: ServerWrapper) -> None:
        self.on_add_service_called = True
        self.services.append(service_name)

    async def on_stop(self) -> None:
        self.on_stop_called = True

from typing_extensions import Any, Protocol


class ServerPlugin(Protocol):

    def on_add_service(self, service_name: str, server: Any) -> None:
        pass

    def on_start(self) -> None:
        pass

    def on_stop(self) -> None:
        pass

from typing_extensions import Any, Protocol

from grpcAPI.singleton import SingletonMeta


class ServerPlugin(Protocol, metaclass=SingletonMeta):

    def on_add_service(self, service_name: str, server: Any) -> None:
        pass

    def on_start(self) -> None:
        pass

    def on_stop(self) -> None:
        pass

from collections.abc import AsyncGenerator

from makeproto import IService
from typing_extensions import (
    Any,
    Callable,
    List,
    Mapping,
    Optional,
    Protocol,
    Sequence,
    Tuple,
    Type,
)


class ProcessService(Protocol):

    def __call__(self, service: IService) -> None: ...


class Labeled(Protocol):
    comments: str
    title: str
    description: str
    tags: List[str]


class SeverFactory(Protocol):
    def __call__(
        self,
        options: Sequence[Tuple[str, Any]],
        middlewares: Optional[Sequence[Any]] = None,
        plugins: Optional[Sequence["ServerPlugin"]] = None,
        settings: Optional[Mapping[str, Any]] = None,
        block_wait: bool = True,
    ) -> "ServerContext": ...


class ServerContext(Protocol):
    """"""

    @property
    def grpc_server(self) -> Any: ...

    def register_service_event(self, service_name: str) -> None: ...
    def add_service(self, service: Type[Any], *args: Any) -> None: ...
    async def start(
        self,
        host: str,
        port: int,
        lifespan: Optional[Callable[["ServerContext"], AsyncGenerator[None, None]]],
        *args: Any,
    ) -> None: ...

    async def stop(self, grace: Optional[float]) -> None: ...


class ServerPlugin(Protocol):
    """"""

    plugin_name: str

    def configure(
        self, context: ServerContext, settings: Mapping[str, Any]
    ) -> None: ...
    def on_add_service(self, service_name: str) -> None: ...
    def on_start(self) -> None: ...
    def on_stop(self) -> None: ...

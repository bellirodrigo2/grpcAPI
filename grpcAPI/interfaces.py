from collections.abc import AsyncGenerator
from logging import Logger
from pathlib import Path
from types import ModuleType

from makeproto import IService
from typing_extensions import (
    Any,
    AsyncIterator,
    Awaitable,
    Callable,
    List,
    Mapping,
    Optional,
    Protocol,
    Sequence,
    Tuple,
    Type,
    TypeVar,
    runtime_checkable,
)

from grpcAPI.context import AsyncContext


class ProcessService(Protocol):

    def __call__(self, service: IService) -> None: ...


class ProcessServiceFactory(Protocol):
    def __call__(self, settings: Mapping[str, Any]) -> ProcessService: ...


class Labeled(Protocol):
    comments: str
    title: str
    description: str
    tags: List[str]


@runtime_checkable
class ServiceModule(Protocol):
    """"""

    module: ModuleType

    def get_service_baseclass(self, service_name: str) -> Optional[Type[Any]]: ...
    def get_add_server(self, service_name: str) -> Callable[..., Any]: ...

    @classmethod
    def proto_to_pymodule(cls, name: str) -> str: ...

    @classmethod
    def make(cls, module: ModuleType) -> "ServiceModule": ...


class ValidateSignaturePass(Protocol):
    """"""

    def __call__(
        self,
        func: Callable[..., Any],
        type_cast: Optional[Sequence[Tuple[Type[Any], Type[Any]]]] = None,
    ) -> Sequence[str]: ...


class SeverFactory(Protocol):
    def __call__(
        self,
        options: Sequence[Tuple[str, Any]],
        middlewares: Optional[Sequence["Middleware"]] = None,
        plugins: Optional[Sequence["ServerPlugin"]] = None,
        settings: Optional[Mapping[str, Any]] = None,
        block_wait: bool = True,
    ) -> "ServerContext": ...


class ServerContext(Protocol):
    """"""

    @property
    def grpc_server(self) -> Any: ...

    def register_service_event(self, service_name: str) -> None: ...
    def add_service(self, service: Type[Any]) -> None: ...
    async def start(
        self,
        host: str,
        port: int,
        lifespan: Optional[Callable[["ServerContext"], AsyncGenerator[None, None]]],
    ) -> None: ...


class CompileProto(Protocol):
    def __call__(
        self,
        root: Path,
        dst: Path,
        clss: bool,
        services: bool,
        mypy_stubs: bool,
        files: Optional[Sequence[str]],
        logger: Logger,
    ) -> None: ...


class ServerPlugin(Protocol):
    """"""

    plugin_name: str

    def configure(
        self, context: ServerContext, settings: Mapping[str, Any]
    ) -> None: ...
    def on_add_service(self, service_name: str) -> None: ...
    def on_start(self) -> None: ...


class GetPackage(Protocol):
    """"""

    def __call__(self, cls: Type[Any]) -> str: ...


class GetProtofilePath(Protocol):
    """"""

    def __call__(self, cls: Type[Any]) -> str: ...


class Validator(Protocol):

    @property
    def casting_list(self) -> Sequence[Tuple[Type[Any], Type[Any]]]: ...

    def inject_validation(self, func: Callable[..., Any]) -> None: ...


Req = TypeVar("Req")
Res = TypeVar("Res")


class Middleware(Protocol):
    async def intercept_unary(
        self,
        call_next: Callable[[Req, AsyncContext], Awaitable[Res]],
        request: Req,
        context: AsyncContext,
    ) -> Res: ...

    async def intercept_client_stream(
        self,
        call_next: Callable[[AsyncIterator[Req], AsyncContext], Awaitable[Res]],
        request_iterator: AsyncIterator[Req],
        context: AsyncContext,
    ) -> Res: ...

    async def intercept_server_stream(
        self,
        call_next: Callable[[Req, AsyncContext], AsyncIterator[Res]],
        request: Req,
        context: AsyncContext,
        # details: grpc.HandlerCallDetails,
    ) -> AsyncIterator[Res]: ...

    async def intercept_bilateral_stream(
        self,
        call_next: Callable[[AsyncIterator[Req], AsyncContext], AsyncIterator[Res]],
        request_iterator: AsyncIterator[Req],
        context: AsyncContext,
    ) -> AsyncIterator[Res]: ...

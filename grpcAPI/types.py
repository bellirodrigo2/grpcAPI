from dataclasses import dataclass

import grpc
from ctxinject.model import Depends as InnerDepends
from ctxinject.model import ModelFieldInject
from google.protobuf.message import Message
from typing_extensions import (
    Any,
    Callable,
    Iterable,
    List,
    Mapping,
    NoReturn,
    Optional,
    Protocol,
    Sequence,
    Tuple,
    Type,
    runtime_checkable,
)

from grpcAPI.makeproto import ILabeledMethod, IMetaType


class Depends(InnerDepends):
    pass


class FromContext(ModelFieldInject):
    def __init__(self, field: Optional[str] = None, **meta: Any):
        super().__init__(model=AsyncContext, field=field, **meta)


class FromRequest(ModelFieldInject):
    def __init__(self, model: Type[Message], field: Optional[str] = None, **meta: Any):
        super().__init__(model=model, field=field, **meta)


@dataclass
class LabeledMethod(ILabeledMethod):
    title: str
    name: str
    method: Callable[..., Any]
    package: str
    module: str
    service: str
    comments: str
    description: str
    options: List[str]
    tags: List[str]

    request_types: List[IMetaType]
    response_types: Optional[IMetaType]


@runtime_checkable
class AsyncContext(Protocol):
    async def read(self) -> Any: ...
    async def write(self, message: Any) -> None: ...
    async def send_initial_metadata(
        self, initial_metadata: Sequence[Tuple[str, str]]
    ) -> None: ...
    async def abort(
        self,
        code: grpc.StatusCode,
        details: str = "",
        trailing_metadata: Sequence[Tuple[str, str]] = tuple(),
    ) -> NoReturn: ...
    def set_trailing_metadata(
        self, trailing_metadata: Sequence[Tuple[str, str]]
    ) -> None: ...
    def invocation_metadata(self) -> Optional[Sequence[Tuple[str, str]]]: ...
    def set_code(self, code: grpc.StatusCode) -> None: ...
    def set_details(self, details: str) -> None: ...
    def set_compression(self, compression: grpc.Compression) -> None: ...
    def disable_next_message_compression(self) -> None: ...
    def peer(self) -> str: ...
    def peer_identities(self) -> Optional[Iterable[bytes]]: ...
    def peer_identity_key(self) -> Optional[str]: ...
    def auth_context(self) -> Mapping[str, Iterable[bytes]]: ...
    def time_remaining(self) -> float: ...
    def trailing_metadata(self) -> Sequence[Tuple[str, str]]: ...
    def code(self) -> str: ...
    def details(self) -> str: ...
    def add_done_callback(self, callback: Callable[..., None]) -> None: ...
    def cancelled(self) -> bool: ...
    def done(self) -> bool: ...

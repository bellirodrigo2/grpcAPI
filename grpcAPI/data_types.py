import grpc
from google.protobuf.message import Message
from google.protobuf.wrappers_pb2 import (
    BoolValue,
    BytesValue,
    DoubleValue,
    FloatValue,
    Int32Value,
    Int64Value,
    StringValue,
    UInt32Value,
    UInt64Value,
)
from typing_extensions import (
    Any,
    Callable,
    Iterable,
    Mapping,
    NoReturn,
    Optional,
    Protocol,
    Sequence,
    Tuple,
    Type,
    runtime_checkable,
)

from grpcAPI.proto_ctxinject import DependsInject, ModelFieldInject
from grpcAPI.prototypes.lib.prototypes_pb2 import (
    ListBool,
    ListBytes,
    ListDouble,
    ListInt,
    ListStr,
    MapIntBytes,
    MapIntStr,
    MapStrBytes,
    MapStrStr,
)


class Depends(DependsInject):
    pass


class FromContext(ModelFieldInject):
    def __init__(self, field: Optional[str] = None, **meta: Any):
        super().__init__(model=AsyncContext, field=field, **meta)


class FromRequest(ModelFieldInject):
    def __init__(self, model: Type[Message], field: Optional[str] = None, **meta: Any):
        super().__init__(model=model, field=field, **meta)


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


# WellKnown types


class _ProtoTypes(ModelFieldInject):
    def __init__(self, model: Type[Message], **meta: Any):
        super().__init__(model=model, field="value", **meta)


class ProtoString(_ProtoTypes):
    def __init__(self, **meta: Any):
        super().__init__(model=StringValue, **meta)


class ProtoBytes(_ProtoTypes):
    def __init__(self, **meta: Any):
        super().__init__(model=BytesValue, **meta)


class ProtoBool(_ProtoTypes):
    def __init__(self, **meta: Any):
        super().__init__(model=BoolValue, **meta)


class ProtoDouble(_ProtoTypes):
    def __init__(self, **meta: Any):
        super().__init__(model=DoubleValue, **meta)


class ProtoFloat(_ProtoTypes):
    def __init__(self, **meta: Any):
        super().__init__(model=FloatValue, **meta)


class ProtoInt64(_ProtoTypes):
    def __init__(self, **meta: Any):
        super().__init__(model=Int64Value, **meta)


class ProtoInt(ProtoInt64): ...


class ProtoUInt64(_ProtoTypes):
    def __init__(self, **meta: Any):
        super().__init__(model=UInt64Value, **meta)


class ProtoInt32(_ProtoTypes):
    def __init__(self, **meta: Any):
        super().__init__(model=Int32Value, **meta)


class ProtoUInt32(_ProtoTypes):
    def __init__(self, **meta: Any):
        super().__init__(model=UInt32Value, **meta)


class ProtoListStr(_ProtoTypes):
    def __init__(self, **meta: Any):
        super().__init__(model=ListStr, **meta)


class ProtoListInt(_ProtoTypes):
    def __init__(self, **meta: Any):
        super().__init__(model=ListInt, **meta)


class ProtoListBool(_ProtoTypes):
    def __init__(self, **meta: Any):
        super().__init__(model=ListBool, **meta)


class ProtoListDouble(_ProtoTypes):
    def __init__(self, **meta: Any):
        super().__init__(model=ListDouble, **meta)


class ProtoListBytes(_ProtoTypes):
    def __init__(self, **meta: Any):
        super().__init__(model=ListBytes, **meta)


class ProtoMapStrStr(_ProtoTypes):
    def __init__(self, **meta: Any):
        super().__init__(model=MapStrStr, **meta)


class ProtoMapStrBytes(_ProtoTypes):
    def __init__(self, **meta: Any):
        super().__init__(model=MapStrBytes, **meta)


class ProtoMapIntStr(_ProtoTypes):
    def __init__(self, **meta: Any):
        super().__init__(model=MapIntStr, **meta)


class ProtoMapIntBytes(_ProtoTypes):
    def __init__(self, **meta: Any):
        super().__init__(model=MapIntBytes, **meta)

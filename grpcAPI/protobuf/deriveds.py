# pragma: no cover
from google.protobuf.wrappers_pb2 import (
    BoolValue,
    BytesValue,
    FloatValue,
    Int64Value,
    StringValue,
)
from typing_extensions import Annotated, Any, Callable, Mapping, Optional, Type

from grpcAPI.datatypes import FromContext, FromRequest


class FromValueField(FromRequest):
    def __init__(
        self,
        model: Type[Any],
        validator: Optional[Callable[..., Any]] = None,
        **meta: Any,
    ):
        super().__init__(model=model, field="value", validator=validator, **meta)


class FromStr(FromValueField):
    def __init__(self, validator: Optional[Callable[..., Any]] = None, **meta: Any):
        super().__init__(model=StringValue, validator=validator, **meta)


class FromInteger(FromValueField):
    def __init__(self, validator: Optional[Callable[..., Any]] = None, **meta: Any):
        super().__init__(model=Int64Value, validator=validator, **meta)


class FromBytes(FromValueField):
    def __init__(self, validator: Optional[Callable[..., Any]] = None, **meta: Any):
        super().__init__(model=BytesValue, validator=validator, **meta)


class FromBoolean(FromValueField):
    def __init__(self, validator: Optional[Callable[..., Any]] = None, **meta: Any):
        super().__init__(model=BoolValue, validator=validator, **meta)


class FromFloat(FromValueField):
    def __init__(self, validator: Optional[Callable[..., Any]] = None, **meta: Any):
        super().__init__(model=FloatValue, validator=validator, **meta)


String = Annotated[str, FromStr()]
Integer = Annotated[int, FromInteger()]
Float = Annotated[float, FromFloat()]
Bytes = Annotated[bytes, FromBytes()]
Boolean = Annotated[bool, FromBoolean()]


class ContextMetadata(FromContext):
    def __init__(self, **meta: Any):
        super().__init__(field="invocation_metadata", validator=dict, **meta)


Metadata = Annotated[Mapping[str, str], ContextMetadata()]

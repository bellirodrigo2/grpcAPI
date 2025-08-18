from typing import Any, Callable, Dict, List, Optional, Type

from google.protobuf.wrappers_pb2 import StringValue
from typing_extensions import Annotated

from grpcAPI.data_types import FromContext, FromRequest
from grpcAPI.protobuf.lib.prototypes_pb2 import KeyValueStr, ListStr


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


class FromKey(FromRequest):
    def __init__(self, validator: Optional[Callable[..., Any]] = None, **meta: Any):
        super().__init__(model=KeyValueStr, field="key", validator=validator, **meta)


class FromValue(FromValueField):
    def __init__(self, validator: Optional[Callable[..., Any]] = None, **meta: Any):
        super().__init__(model=KeyValueStr, validator=validator, **meta)


class FromListStr(FromValueField):
    def __init__(self, validator: Optional[Callable[..., Any]] = None, **meta: Any):
        super().__init__(model=ListStr, validator=validator, **meta)


ProtoStr = Annotated[str, FromStr()]
ProtoKey = Annotated[str, FromKey()]
ProtoValue = Annotated[str, FromValue()]
ProtoListStr = Annotated[List[str], FromListStr()]


class ContextMetadata(FromContext):
    def __init__(self, **meta: Any):
        super().__init__(field="invocation_metadata", validator=dict, **meta)


Metadata = Annotated[Dict[str, str], ContextMetadata()]

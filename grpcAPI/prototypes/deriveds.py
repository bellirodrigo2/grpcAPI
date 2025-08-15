from typing import Any, List, Type
from typing_extensions import Annotated
from grpcAPI.prototypes import KeyValueStr, StringValue,ListStr
from grpcAPI.data_types import FromRequest

class FromValueField(FromRequest):
    def __init__(self, model:Type[Any]):
        super().__init__(KeyValueStr, field='value')

class FromStr(FromValueField):
    def __init__(self):
        super().__init__(StringValue)

class FromKey(FromRequest):
    def __init__(self):
        super().__init__(KeyValueStr, field='key')

class FromValue(FromValueField):
    def __init__(self):
        super().__init__(KeyValueStr, )
        
class FromListStr(FromValueField):
    def __init__(self):
        super().__init__(ListStr)

ProtoStr = Annotated[str, FromStr()]
ProtoKey = Annotated[str, FromKey()]
ProtoValue = Annotated[str, FromValue()]
ProtoListStr = Annotated[List[str], FromListStr()]
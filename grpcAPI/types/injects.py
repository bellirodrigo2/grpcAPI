from ctxinject.model import Depends as inner_Depends
from ctxinject.model import ModelFieldInject
from typing_extensions import Any, Optional, Type

from grpcAPI.types import BaseContext, Message


class Depends(inner_Depends):
    pass


class FromContext(ModelFieldInject):
    def __init__(self, field: Optional[str] = None, **meta: Any):
        super().__init__(model=BaseContext, field=field, **meta)


class FromRequest(ModelFieldInject):
    def __init__(self, model: Type[Message], field: Optional[str] = None, **meta: Any):
        super().__init__(model=model, field=field, **meta)

from typing import Any, Optional

from ctxinject.model import Depends as inner_Depends
from ctxinject.model import ModelFieldInject

from grpcAPI.types import Message
from grpcAPI.types.context import BaseContext


class Depends(inner_Depends):
    pass


class FromContext(ModelFieldInject):
    def __init__(self, field: Optional[str] = None, **meta: Any):
        super().__init__(model=BaseContext, field=field, **meta)


class FromRequest(ModelFieldInject):
    def __init__(self, model: Message, field: Optional[str] = None, **meta: Any):
        super().__init__(model=model, field=field, **meta)

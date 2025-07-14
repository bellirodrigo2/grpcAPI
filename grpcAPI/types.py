from dataclasses import dataclass

from ctxinject.model import Depends as InnerDepends
from ctxinject.model import ModelFieldInject
from makeproto import ILabeledMethod, IMetaType
from typing_extensions import Any, Callable, List, Optional, Type

from grpcAPI.config import MESSAGE_TYPE as Message
from grpcAPI.context import BaseContext


class Depends(InnerDepends):
    pass


class FromContext(ModelFieldInject):
    def __init__(self, field: Optional[str] = None, **meta: Any):
        super().__init__(model=BaseContext, field=field, **meta)


class FromRequest(ModelFieldInject):
    def __init__(self, model: Type[Message], field: Optional[str] = None, **meta: Any):
        super().__init__(model=model, field=field, **meta)


@dataclass
class LabeledMethod(ILabeledMethod):
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

from functools import partial
from typing import Any, Callable, List, Optional

from typemapping import get_func_args

from grpcAPI.app import ProtoModel
from grpcAPI.ctxinject.model import ModelFieldInject
from grpcAPI.ctxinject.sigcheck import func_signature_check
from grpcAPI.types import Context, Stream
from grpcAPI.types.message import is_BaseMessage


class FromContext(ModelFieldInject):
    def __init__(self, field: Optional[str] = None, **meta: Any):
        super().__init__(model=Context, field=field, **meta)


class FromRequest(ModelFieldInject):
    pass


validate_injectable_function = partial(
    func_signature_check, modeltype=[ProtoModel, Context], generictype=Stream
)


def extract_request(func: Callable[..., Any]) -> List[type]:
    funcargs = get_func_args(func)
    requests = set()

    for arg in funcargs:
        instance = arg.getinstance(FromRequest)
        if is_BaseMessage(arg.basetype):
            requests.add(arg.basetype)
        elif instance is not None:
            requests.add(instance.model)

    return list(requests)

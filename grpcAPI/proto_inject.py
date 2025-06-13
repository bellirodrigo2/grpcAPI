from functools import partial
from typing import Any, Callable, List, Mapping, Optional, Sequence, Union
from urllib import request

from grpcAPI.ctxinject.model import ModelFieldInject
from grpcAPI.ctxinject.validate import func_signature_validation
from grpcAPI.proto_proxy import ProtoProxy
from grpcAPI.typemapping import VarTypeInfo, get_func_args
from grpcAPI.types import Context
from grpcAPI.types.method import Stream


class FromContext(ModelFieldInject):
    def __init__(self, field: Optional[str] = None, **meta: Any):
        super().__init__(model=Context, field=field, **meta)


class FromRequest(ModelFieldInject):
    pass


def extract_request_model(
    args: Sequence[VarTypeInfo], ctx: Mapping[Union[str, type], Any]
) -> Sequence[VarTypeInfo]:

    def get_protoproxy(ctx: Mapping[Union[str, type], Any]) -> type[ProtoProxy]:
        req_type = [
            btype
            for btype in ctx.keys()
            if isinstance(btype, type) and issubclass(btype, ProtoProxy)
        ]
        if len(req_type) != 1:
            raise TypeError
        return req_type[0]

    req_type = get_protoproxy(ctx)

    for arg in args:
        instance = arg.getinstance(ModelFieldInject)
        if instance is not None and instance.model is None:
            instance.model = req_type

    return args


validate_injectable_function = partial(
    func_signature_validation, modeltype=[ProtoProxy, Context], generictype=Stream
)


def extract_request(func: Callable[..., Any]) -> List[type]:
    funcargs = get_func_args(func)
    requests = set(
        [
            arg.basetype
            for arg in funcargs
            if arg.istype(ProtoProxy) and arg.basetype is not None
        ]
    )

    for arg in funcargs:
        instance = arg.getinstance(FromRequest)
        if instance is not None:
            requests.add(instance.model)

    return list(requests)

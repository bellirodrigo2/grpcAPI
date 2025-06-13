from typing import Any, Mapping, Optional, Sequence, Union

from grpcAPI.ctxinject.model import ModelFieldInject
from grpcAPI.proto_proxy import ProtoProxy
from grpcAPI.typemapping import VarTypeInfo
from grpcAPI.types.context import Context


class FromContext(ModelFieldInject):
    def __init__(self, field: Optional[str] = None, **meta: Any):
        super().__init__(model=Context, field=field, **meta)


class FromRequest(ModelFieldInject):
    def __init__(self, field: Optional[str] = None, **meta: Any):
        super().__init__(model=None, field=field, **meta)


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

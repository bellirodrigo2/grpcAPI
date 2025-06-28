from functools import partial
from typing import Any, Callable, Dict, List, Optional, Tuple, Type

from typemapping import get_func_args, map_return_type

from grpcAPI.ctxinject.model import ModelFieldInject
from grpcAPI.ctxinject.sigcheck import func_signature_check
from grpcAPI.ctxinject.validate import inject_validation
from grpcAPI.proto_proxy import ProtoModel
from grpcAPI.types import Context, Stream, is_BaseMessage


class FromContext(ModelFieldInject):
    def __init__(self, field: Optional[str] = None, **meta: Any):
        super().__init__(model=Context, field=field, **meta)


class FromRequest(ModelFieldInject):
    pass


def proto_check_injectable(
    func: Callable[..., Any],
    type_cast: Optional[List[Tuple[type[Any], Type[Any]]]] = None,
) -> List[str]:
    type_cast = type_cast or []
    return func_signature_check(
        func,
        modeltype=[ProtoModel, Context],
        generictype=Stream,
        bt_default_fallback=True,
        type_cast=type_cast,
    )


def define_validation_function(
    type_cast: List[Tuple[type[Any], Type[Any]]],
) -> Callable[..., Any]:
    return partial(proto_check_injectable, type_cast=type_cast)


def proto_inject_validation(
    func: Callable[..., Any],
    argproc: Dict[Tuple[type[Any], Type[Any]], Callable[..., Any]],
) -> Callable[..., Any]:
    inject_validation(func, argproc)
    return func


def extract_request(func: Callable[..., Any]) -> List[Type[Any]]:
    funcargs = get_func_args(func)
    requests = set()

    for arg in funcargs:
        instance = arg.getinstance(FromRequest)
        if is_BaseMessage(arg.basetype):
            requests.add(arg.basetype)
        elif instance is not None:
            model = instance.model
            if not isinstance(model, type) or not issubclass(model, ProtoModel):
                raise TypeError(
                    f'On function "{func.__name__}", argument "{arg.name}", FromRequest uses an invalid model: "{model}"'
                )
            requests.add(model)

    return list(requests)


def get_return_type(func: Callable[..., Any]) -> Type[Any]:
    returntype = map_return_type(func)
    return returntype.basetype


def extract_models(func: Callable[..., Any]) -> Tuple[Type[Any], Type[Any]]:
    request_types = extract_request(func)
    if len(request_types) != 1 or not is_BaseMessage(request_types[0]):
        raise TypeError(f"Request Model is not valid: {request_types}")
    request_type = request_types[0]
    response_type = get_return_type(func)
    return request_type, response_type

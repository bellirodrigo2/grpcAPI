from collections.abc import AsyncIterator

from ctxinject.sigcheck import func_signature_check
from google.protobuf.internal.enum_type_wrapper import EnumTypeWrapper
from typemapping import VarTypeInfo, get_func_args
from typing_extensions import Any, Callable, List, Optional, Tuple, Type

from grpcAPI.protobut_typing import inject_proto_typing
from grpcAPI.types import AsyncContext, FromRequest, Message


def validate_signature_pass(
    func: Callable[..., Any],
    type_cast: Optional[List[Tuple[Type[Any], Type[Any]]]] = None,
) -> List[str]:
    inject_typing(func)
    return func_signature_check(
        func, [Message, AsyncContext], AsyncIterator, True, type_cast
    )


def is_enum(arg: VarTypeInfo) -> bool:
    if isinstance(arg.basetype, EnumTypeWrapper):
        return True
    if arg.origin is list and isinstance(arg.args[0], EnumTypeWrapper):
        return True
    if arg.origin is dict and isinstance(arg.args[1], EnumTypeWrapper):
        return True
    return False


def inject_typing(transform_func: Callable[..., Any]) -> Callable[..., Any]:
    args = get_func_args(transform_func)

    for arg in args:
        instance = arg.getinstance(FromRequest)
        if instance is None:
            continue
        model = instance.model

        annotations = inject_proto_typing(model)

        if annotations is not None:
            model.__annotations__ = annotations

        if is_enum(arg):
            model.__annotations__[arg.name] = arg.basetype
    return transform_func

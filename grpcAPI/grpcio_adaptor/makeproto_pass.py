from collections.abc import AsyncIterator

from ctxinject.sigcheck import func_signature_check
from google.protobuf.internal.enum_type_wrapper import EnumTypeWrapper
from typemapping import get_func_args
from typing_extensions import Any, Callable, List

from grpcAPI.grpcio_adaptor.protobut_typing import inject_proto_typing
from grpcAPI.types import BaseContext, FromRequest, Message


def validate_signature_pass(func: Callable[..., Any]) -> List[str]:
    """Implementarion for MethodSigValidation using grpcio and ctxinject"""
    inject_typing(func)
    return func_signature_check(func, [Message, BaseContext], AsyncIterator)


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

        if isinstance(arg.basetype, EnumTypeWrapper):
            model.__annotations__[arg.name] = arg.basetype
    return transform_func

from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any, Callable, List, Optional, Set, Type, get_args, get_origin

from ctxinject.validate import func_signature_validation
from makeproto import ILabeledMethod, IMetaType
from typemapping import get_func_args, map_return_type

from grpcAPI.types import Context, FromRequest, Message


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


@dataclass
class MetaType(IMetaType):
    argtype: Type[Any]
    basetype: Type[Any]
    origin: Optional[Type[Any]]
    package: str
    proto_path: str


def label_method(
    func: Callable[..., Any],
    package: str,
    module: str,
    service: str,
    method_name: str,
    comment: str,
    description: str,
    options: List[str],
    tags: List[str],
) -> LabeledMethod:

    request_args = extract_request(func)
    requests = [type_to_metatype(arg) for arg in request_args]

    response_arg = extract_response(func)

    if response_arg is None:
        response_type = None
    else:
        response_type = type_to_metatype(response_arg)

    return LabeledMethod(
        name=method_name,
        method=func,
        package=package,
        module=module,
        service=service,
        comments=comment,
        description=description,
        request_types=requests,
        response_types=response_type,
        options=options,
        tags=tags,
    )


def type_to_metatype(varinfo: Type[Any]) -> IMetaType:

    argtype = varinfo
    origin = get_origin(varinfo)
    basetype = varinfo if origin is None else get_args(varinfo)[0]

    package = get_package(basetype)
    proto_path = get_protofile_relative_path(basetype)

    return MetaType(
        argtype=argtype,
        basetype=basetype,
        origin=origin,
        package=package,
        proto_path=proto_path,
    )


def get_protofile_relative_path(cls: Type[Any]) -> str:
    return cls.DESCRIPTOR.file.name


def get_package(cls: Type[Any]) -> str:
    return cls.DESCRIPTOR.file.package


def extract_request(func: Callable[..., Any]) -> List[Type[Any]]:
    funcargs = get_func_args(func)
    requests: Set[Type[Any]] = set()

    for arg in funcargs:
        instance = arg.getinstance(FromRequest)
        if get_message(arg.basetype):
            requests.add(arg.basetype)
        elif instance is not None:
            model = instance.model
            if not is_message(model):
                raise TypeError(
                    f'On function "{func.__name__}", argument "{arg.name}", FromRequest uses an invalid model: "{model}"'
                )
            requests.add(model)

    return list(requests)


def extract_response(func: Callable[..., Any]) -> Optional[Type[Any]]:
    returnvartype = map_return_type(func)
    returntype = returnvartype.basetype
    return returntype if get_message(returntype) else None


def is_message(bt: Optional[Type[Any]]) -> bool:
    if bt is None:
        return False
    return isinstance(bt, type) and issubclass(bt, Message)  # type: ignore


def if_stream_get_type(bt: Type[Any]) -> Optional[type[Any]]:
    if get_origin(bt) is AsyncIterator:
        return get_args(bt)[0]
    return bt


def get_message(tgt: Optional[Type[Any]]) -> Optional[type[Any]]:

    if tgt is None:
        return None

    basetype = if_stream_get_type(tgt)
    if is_message(basetype):
        return basetype
    return None


def validate_signature(func: Callable[..., Any]) -> List[str]:
    return func_signature_validation(func, [Message, Context], AsyncIterator)

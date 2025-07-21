from collections.abc import AsyncIterator
from dataclasses import dataclass

from makeproto import IMetaType
from typemapping import get_func_args, map_return_type
from typing_extensions import (
    Any,
    Callable,
    List,
    Optional,
    Set,
    Tuple,
    Type,
    get_args,
    get_origin,
)

from grpcAPI.types import FromRequest, Message


def get_protofile_path(cls: Type[Any]) -> str:
    return cls.DESCRIPTOR.file.name


def get_package(cls: Type[Any]) -> str:
    return cls.DESCRIPTOR.file.package


def extract_request_response_type(
    func: Callable[..., Any],
) -> Tuple[List[IMetaType], Optional[IMetaType]]:
    request_args = extract_request(func)
    requests = [type_to_metatype(arg) for arg in request_args]

    response_arg = extract_response(func)

    if response_arg is None:
        response_type = None
    else:
        response_type = type_to_metatype(response_arg)
    return requests, response_type


@dataclass
class MetaType(IMetaType):
    argtype: Type[Any]
    basetype: Type[Any]
    origin: Optional[Type[Any]]
    package: str
    proto_path: str

    def __str__(self) -> str:
        cls = self.basetype
        cls_name = f"{cls.__module__}.{cls.__qualname__}"
        if self.origin is None:
            final_str = cls_name
        else:
            final_str = f"{self.origin.__name__}[{cls_name}]"
        return f"<{final_str}>"


def type_to_metatype(varinfo: Type[Any]) -> IMetaType:

    argtype = varinfo
    origin = get_origin(varinfo)
    basetype = varinfo if origin is None else get_args(varinfo)[0]

    package = get_package(basetype)
    proto_path = get_protofile_path(basetype)

    return MetaType(
        argtype=argtype,
        basetype=basetype,
        origin=origin,
        package=package,
        proto_path=proto_path,
    )


def extract_request(func: Callable[..., Any]) -> List[Type[Any]]:
    funcargs = get_func_args(func)
    requests: Set[Type[Any]] = set()

    for arg in funcargs:
        instance = arg.getinstance(FromRequest)
        if instance is not None:
            model = instance.model
            if not is_message(model):
                raise TypeError(
                    f'On function "{func.__name__}", argument "{arg.name}", FromRequest uses an invalid model: "{model}"'
                )
            requests.add(model)
        elif get_message(arg.basetype):
            requests.add(arg.basetype)

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

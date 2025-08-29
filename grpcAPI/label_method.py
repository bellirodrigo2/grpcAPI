from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Dict

from typemapping import get_func_args, map_return_type
from typing_extensions import (
    Any,
    Callable,
    List,
    Optional,
    Set,
    Type,
    get_args,
    get_origin,
)

from grpcAPI.data_types import FromRequest, Message, set_function_metadata
from grpcAPI.makeproto import ILabeledMethod, IMetaType


def get_protofile_path(cls: Type[Any]) -> str:
    return cls.DESCRIPTOR.file.name


def get_package(cls: Type[Any]) -> str:
    return cls.DESCRIPTOR.file.package


@dataclass
class LabeledMethod(ILabeledMethod):
    title: str
    name: str
    method: Callable[..., Any]
    package: str
    module: str
    service: str
    comments: str
    description: str
    options: List[str]
    tags: List[str]
    meta: Dict[str, Any]

    request_types: List[IMetaType]
    response_types: Optional[IMetaType]
    _active: bool = True

    @property
    def active(self) -> bool:
        return self._active

    @active.setter
    def active(self, value: bool) -> None:
        self._active = value

    @property
    def input_type(self) -> Type[Any]:
        if not self.request_types:
            raise ValueError("No request types available")
        return self.request_types[0].argtype

    @property
    def output_type(self) -> Type[Any]:
        if not self.response_types:
            raise ValueError("No response types available")
        return self.response_types.argtype

    @property
    def is_client_stream(self) -> bool:
        if not self.request_types:
            raise ValueError("No request types available")
        req = self.request_types[0]
        return req.origin is AsyncIterator

    @property
    def is_server_stream(self) -> bool:
        resp = self.response_types
        if resp is None:
            raise ValueError("No response types available")
        return resp.origin is AsyncIterator

    @property
    def input_base_type(self) -> Type[Any]:
        if self.is_client_stream:
            if not self.request_types:
                raise ValueError("No request types available")
            return self.request_types[0].basetype
        return self.input_type

    @property
    def output_base_type(self) -> Type[Any]:
        if self.is_server_stream:
            if not self.response_types:
                raise ValueError("No response types available")
            return self.response_types.basetype
        return self.output_type


def make_labeled_method(
    title: str,
    func: Callable[..., Any],
    package: str,
    module: str,
    service: str,
    comment: str,
    description: str,
    meta: Dict[str, Any],
    tags: Optional[List[str]] = None,
    options: Optional[List[str]] = None,
    request_type_input: Optional[Type[Any]] = None,
    response_type_input: Optional[Type[Any]] = None,
) -> ILabeledMethod:
    if request_type_input is not None and is_message(request_type_input):
        requests = [type_to_metatype(request_type_input)]
        set_function_metadata(func, request_type_input)
    else:
        requests = extract_request_type(func)

    response_type = extract_response_type(func, response_type_input)

    method_name = func.__name__
    tags = tags or []
    options = options or []

    return LabeledMethod(
        title=title,
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
        meta=meta,
    )


def extract_request_type(
    func: Callable[..., Any],
) -> List[IMetaType]:
    request_args = extract_request(func)
    requests = [type_to_metatype(arg) for arg in request_args]
    return requests


def extract_response_type(
    func: Callable[..., Any],
    response_type_input: Optional[Type[Any]] = None,
) -> Optional[IMetaType]:
    response_arg = extract_response(func) or response_type_input
    if response_arg is None:
        return None

    return type_to_metatype(response_arg)


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


def if_stream_get_type(bt: Type[Any]) -> Optional[Type[Any]]:
    if get_origin(bt) is AsyncIterator:
        return get_args(bt)[0]
    return bt


def get_message(tgt: Optional[Type[Any]]) -> Optional[Type[Any]]:

    if tgt is None:
        return None

    basetype = if_stream_get_type(tgt)
    if is_message(basetype):
        return basetype
    return None

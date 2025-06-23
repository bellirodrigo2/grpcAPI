from collections import defaultdict
from dataclasses import asdict
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union

from typemapping import get_func_args, map_model_fields, map_return_type

from grpcAPI.makeproto.protoblock import (
    Block,
    EnumBlock,
    EnumField,
    Field,
    MessageBlock,
    Method,
    Node,
    OneOfBlock,
    OneOfField,
    ServiceBlock,
)
from grpcAPI.types import (
    BaseMessage,
    IService,
    Metadata,
    OneOf,
    ProtoOption,
    get_headers,
)


def make_msgblock(cls: type[BaseMessage]) -> Block:

    protofile, package, description, options, reserveds = get_headers(cls)

    block = MessageBlock(
        protofile=protofile,
        package=package,
        name=cls.__name__,
        fields=[],
        block=None,
        description=description,
        options=options,
        number=0,
        reserveds=reserveds,
        render_dict={"block_type": "message"},
    )

    fields: List[Node] = []
    oneofs: Dict[str, List[Field]] = defaultdict(list)
    args = map_model_fields(cls, False)
    for arg in args:
        metadata = arg.getinstance(Metadata, True)
        if metadata is None:
            metadata = Metadata()

        field = Field(
            name=arg.name,
            ftype=arg.basetype,
            description=metadata.description,
            options=metadata.options,
            number=metadata.index,
            block=block,
            render_dict={},
        )

        if isinstance(metadata, OneOf):
            key = metadata.key
            field_dict = asdict(field)
            oneof_field = OneOfField(**field_dict, key=key)
            oneofs[key].append(oneof_field)
        else:
            fields.append(field)

    for k, v in oneofs.items():
        ootemp = OneOfBlock(
            protofile=protofile,
            package=package,
            name=k,
            number=0,
            block=block,
            fields=v,
            description="",
            options={},
            reserveds=[],
            render_dict={"block_type": "oneof"},
        )
        for field in v:
            field.block = ootemp
        fields.append(ootemp)

    block.fields = fields

    return block


def make_enumblock(enum: type[BaseMessage]) -> Block:

    protofile, package, description, options, reserveds = get_headers(enum)

    enum_block = EnumBlock(
        protofile=protofile,
        package=package,
        name=enum.__name__,
        fields=[],
        block=None,
        number=0,
        description=description,
        options=options,
        reserveds=reserveds,
        render_dict={"block_type": "enum"},
    )

    fields: List[Field] = []
    for member in enum:
        name, value = member.name, member.value
        fields.append(
            EnumField(
                name=name,
                number=value,
                ftype=None,
                description="",
                options={},
                block=enum_block,
                render_dict={},
            )
        )

    enum_block.fields = fields

    return enum_block


def make_cls_block(cls: type[Union[BaseMessage, Enum]]) -> Block:
    if issubclass(cls, Enum):
        return make_enumblock(cls)
    elif issubclass(cls, BaseMessage):
        return make_msgblock(cls)
    raise TypeError(
        f'Mapping Class "{cls.__name__}" is not BaseMessage or Enum: "{type(cls)}"'
    )


def get_args(
    func: Callable[..., Any],
) -> List[Optional[type[Any]]]:
    args = get_func_args(func)
    return [arg.basetype for arg in args]


def get_return_type(func: Callable[..., Any]) -> type[Any]:
    returntype = map_return_type(func)
    return returntype.basetype


def make_method(
    func: Callable[..., Any],
    block: Optional[ServiceBlock] = None,
    description: str = "",
    options: Optional[ProtoOption] = None,
    getargs: Optional[Callable[[Callable[..., Any]], List[Optional[type[Any]]]]] = None,
) -> Method:

    getargs = getargs or get_args
    req_types = getargs(func)

    returntype = get_return_type(func)
    return Method(
        name=func.__name__,
        request_type=req_types,
        response_type=returntype,
        block=block,
        method_func=func,
        number=0,
        description=description,
        options=options or ProtoOption(),
        render_dict={},
    )


def make_service(
    service: IService,
    getargs: Optional[Callable[[Callable[..., Any]], List[Optional[type[Any]]]]] = None,
) -> ServiceBlock:

    servblock = ServiceBlock(
        name=service.name,
        protofile=service.module,
        package=service.package,
        fields=[],
        number=0,
        block=None,
        options=service.options,
        description=service.description,
        render_dict={"block_type": "service"},
        reserveds=[],
    )
    method_list = [
        make_method(
            method.method,
            servblock,
            method.description,
            method.options,
            getargs or get_args,
        )
        for method in service.methods
    ]
    servblock.fields = method_list
    return servblock

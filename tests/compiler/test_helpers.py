from collections.abc import Callable
from typing import Any, List, Optional, Set, Union

from grpcAPI.makeproto.protoblock import (
    Block,
    EnumBlock,
    EnumField,
    Field,
    MessageBlock,
    Method,
    OneOfBlock,
    OneOfField,
    Service,
)


def make_field(
    name: str,
    block: Optional[Block] = None,
    ftype: Optional[type[Any]] = None,
    number: Optional[int] = None,
) -> Field:
    field = Field(name=name, ftype=ftype, number=number, block=block, render_dict={})
    if block is not None:
        block.fields.append(field)
    return field


def make_enumfield(
    name: str,
    block: Optional[Block] = None,
    number: int = 1,
) -> EnumField:
    field = EnumField(name=name, number=number, block=block, render_dict={})
    if block is not None:
        block.fields.append(field)
    return field


def make_oneof_field(
    name: str,
    block: Optional[Block] = None,
    ftype: Optional[type[Any]] = None,
    number: Optional[int] = None,
) -> OneOfField:
    field = OneOfField(
        name=name, ftype=ftype, number=number, block=block, render_dict={}
    )
    if block is not None:
        block.fields.append(field)
    return field


def make_method(
    name: str,
    block: Optional[Block] = None,
    request_type: List[type[Any]] = [],
    response_type: Optional[type[Any]] = None,
    method_func: Optional[Callable[..., Any]] = None,
) -> Method:
    method = Method(
        name=name,
        request_type=request_type,
        response_type=response_type,
        block=block,
        method_func=method_func,
        number=0,
        render_dict={},
    )

    if block is not None:
        block.fields.append(method)
    return method


def _make_reserved_block(
    name: str,
    fields: Optional[List[Union[Field, Method, Block]]],
    block: Optional[Block],
    reserveds: Optional[Set[Union[str, int]]],
    protofile: str,
    package: str,
    type: str,
) -> Block:
    if type == "service":
        BlockClass = Service
    if type == "enum":
        BlockClass = EnumBlock
    elif type == "oneof":
        BlockClass = OneOfBlock
    else:
        BlockClass = MessageBlock

    newblock = BlockClass(
        name=name,
        fields=fields or [],
        reserveds=reserveds or set(),
        counter=0 if type == "enum" else 1,
        protofile=protofile,
        package=package,
        block=block,
        number=0,
        render_dict={},
    )

    if block is not None:
        block.fields.append(newblock)

    return newblock


def make_enum_block(
    name: str,
    fields: Optional[List[Union[Field, Method, Block]]] = None,
    block: Optional[Block] = None,
    reserveds: Optional[Set[Union[str, int]]] = None,
    protofile: str = "test.proto",
    package: str = "test.package",
) -> Block:
    return _make_reserved_block(
        name, fields, block, reserveds, protofile, package, "enum"
    )


def make_message_block(
    name: str,
    fields: Optional[List[Union[Field, Method, Block]]] = None,
    block: Optional[Block] = None,
    reserveds: Optional[Set[Union[str, int]]] = None,
    protofile: str = "test.proto",
    package: str = "test.package",
) -> MessageBlock:
    return _make_reserved_block(
        name, fields, block, reserveds, protofile, package, "message"
    )


def make_oneof_block(
    name: str,
    fields: Optional[List[Union[Field, Method, Block]]] = None,
    block: Optional[Block] = None,
    protofile: str = "test.proto",
    package: str = "test.package",
) -> OneOfBlock:
    return _make_reserved_block(name, fields, block, set(), protofile, package, "oneof")


def make_service_block(
    name: str,
    fields: Optional[List[Union[Field, Method, Block]]] = None,
    block: Optional[Block] = None,
    protofile: str = "test.proto",
    package: str = "test.package",
) -> Service:
    return _make_reserved_block(
        name, fields, block, set(), protofile, package, "service"
    )

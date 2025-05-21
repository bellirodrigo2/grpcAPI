from typing import Any, Callable, Dict, List, Optional, Set, Union

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


def _make_generic_field(
    name: str,
    block: Optional[Block] = None,
    ftype: Optional[type[Any]] = None,
    number: Optional[int] = None,
    description: str = "",
    options: Optional[Dict[str, Union[str, bool]]] = None,
    type: str = "field",
) -> Field:

    if type == "enum":
        BlockClass = EnumField
    elif type == "oneof":
        BlockClass = OneOfField
    else:
        BlockClass = Field

    field = BlockClass(
        name=name,
        ftype=ftype,
        number=number,
        block=block,
        render_dict={},
        description=description,
        options=options or {},
    )
    if block is not None:
        block.fields.append(field)
    return field


def make_field(
    name: str,
    block: Optional[Block] = None,
    ftype: Optional[type[Any]] = None,
    number: Optional[int] = None,
    description: str = "",
    options: Optional[Dict[str, Union[str, bool]]] = None,
) -> Field:
    return _make_generic_field(name, block, ftype, number, description, options)


def make_enumfield(
    name: str,
    block: Optional[Block] = None,
    number: int = 1,
    description: str = "",
    options: Optional[Dict[str, Union[str, bool]]] = None,
) -> EnumField:
    return _make_generic_field(name, block, None, number, description, options, "enum")


def make_oneof_field(
    name: str,
    block: Optional[Block] = None,
    ftype: Optional[type[Any]] = None,
    number: Optional[int] = None,
    description: str = "",
    options: Optional[Dict[str, Union[str, bool]]] = None,
) -> OneOfField:
    return _make_generic_field(
        name, block, ftype, number, description, options, "oneof"
    )


def make_method(
    name: str,
    block: Optional[Block] = None,
    request_type: Optional[List[type[Any]]] = None,
    response_type: Optional[type[Any]] = None,
    method_func: Optional[Callable[..., Any]] = None,
    description: str = "",
    options: Optional[Dict[str, Union[str, bool]]] = None,
) -> Method:
    method = Method(
        name=name,
        request_type=request_type or [],
        response_type=response_type,
        block=block,
        method_func=method_func,
        number=0,
        render_dict={},
        description=description,
        options=options or {},
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
    description: str = "",
    options: Optional[Dict[str, Union[str, bool]]] = None,
    type: str = "message",
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
        description=description,
        options=options or {},
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
    description: str = "",
    options: Optional[Dict[str, Union[str, bool]]] = None,
) -> Block:
    return _make_reserved_block(
        name, fields, block, reserveds, protofile, package, description, options, "enum"
    )


def make_message_block(
    name: str,
    fields: Optional[List[Union[Field, Method, Block]]] = None,
    block: Optional[Block] = None,
    reserveds: Optional[Set[Union[str, int]]] = None,
    protofile: str = "test.proto",
    package: str = "test.package",
    description: str = "",
    options: Optional[Dict[str, Union[str, bool]]] = None,
) -> MessageBlock:
    return _make_reserved_block(
        name,
        fields,
        block,
        reserveds,
        protofile,
        package,
        description,
        options,
        "message",
    )


def make_oneof_block(
    name: str,
    fields: Optional[List[Union[Field, Method, Block]]] = None,
    block: Optional[Block] = None,
    protofile: str = "test.proto",
    package: str = "test.package",
    description: str = "",
    options: Optional[Dict[str, Union[str, bool]]] = None,
) -> OneOfBlock:
    return _make_reserved_block(
        name, fields, block, set(), protofile, package, description, options, "oneof"
    )


def make_service_block(
    name: str,
    fields: Optional[List[Union[Field, Method, Block]]] = None,
    block: Optional[Block] = None,
    protofile: str = "test.proto",
    package: str = "test.package",
    description: str = "",
    options: Optional[Dict[str, Union[str, bool]]] = None,
) -> Service:
    return _make_reserved_block(
        name, fields, block, set(), protofile, package, description, options, "service"
    )

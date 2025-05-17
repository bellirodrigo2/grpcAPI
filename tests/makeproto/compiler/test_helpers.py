from typing import Any, List, Optional, Set, Union

from grpcAPI.makeproto.block_models import Block, Field, Method


def make_field(
    name: str,
    block: Optional[Block] = None,
    *,
    ftype: Optional[type[Any]] = None,
    number: int = 1,
) -> Field:
    field = Field(
        name=name,
        ftype=ftype,
        number=number,
        block=block,
    )
    if block is not None:
        block.fields.append(field)
    return field


def make_method(
    name: str,
    block: Optional[Block] = None,
    *,
    request_type: Optional[type[Any]] = None,
    response_type: Optional[type[Any]] = None,
    request_stream: bool = False,
    response_stream: bool = False,
) -> Method:
    return Method(
        name=name,
        request_type=request_type,
        response_type=response_type,
        request_stream=request_stream,
        response_stream=response_stream,
        block=block,
    )


def make_block(
    name: str,
    fields: Optional[List[Union[Field, Method, Block]]] = None,
    block: Optional[Block] = None,
    *,
    reserveds: Optional[Set[Union[str, int]]] = None,
    block_type: str = "message",
) -> Block:
    return Block(
        name=name,
        fields=fields or [],
        reserveds=reserveds or set(),
        block_type=block_type,
        protofile="test.proto",
        package="test.package",
        block=block,
    )

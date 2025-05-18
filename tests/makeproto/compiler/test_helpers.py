from collections.abc import Callable
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
    )

    if block is not None:
        block.fields.append(method)
    return method


def make_block(
    name: str,
    fields: Optional[List[Union[Field, Method, Block]]] = None,
    block: Optional[Block] = None,
    *,
    reserveds: Optional[Set[Union[str, int]]] = None,
    block_type: str = "message",
    protofile: str = "test.proto",
    package: str = "test.package",
) -> Block:
    return Block(
        name=name,
        fields=fields or [],
        reserveds=reserveds or set(),
        block_type=block_type,
        protofile=protofile,
        package=package,
        block=block,
    )

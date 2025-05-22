from enum import Enum
from typing import Any, Callable, List, Optional, Set

from grpcAPI.makeproto.makeblock import make_enumblock, make_msgblock
from grpcAPI.makeproto.protoblock import Block
from grpcAPI.mapclass import map_class_fields, map_func_args
from grpcAPI.types import BaseMessage, get_BaseMessage


def cls_map(
    tgt: type[BaseMessage],
    visited: Optional[Set[type[BaseMessage]]] = None,
) -> Set[type[BaseMessage]]:

    if visited is None:
        visited = set()

    if tgt in visited:
        return visited

    if issubclass(tgt, Enum) or issubclass(tgt, BaseMessage):
        visited.add(tgt)

        args = map_class_fields(tgt, False)

        for arg in args:
            if arg.istype(BaseMessage):
                msgs = cls_map(arg.basetype, visited)
                visited.update(msgs)
            elif arg.istype(Enum):
                visited.add(arg.basetype)
    return visited


def cls_to_blocks(tgt: type[BaseMessage]) -> List[Block]:

    clss = cls_map(tgt)

    blocks: List[Block] = []
    for cls in clss:
        if issubclass(cls, Enum):
            enumblock = make_enumblock(cls)
            blocks.append(enumblock)

        elif issubclass(cls, BaseMessage):
            msgblock = make_msgblock(cls)
            blocks.append(msgblock)
    return blocks


def map_service_to_blocks(methods: List[Callable[..., Any]]) -> List[Block]:
    all_types: Set[type] = set()

    for method in methods:
        funcargs, return_type = map_func_args(method)
        for arg in funcargs:
            base = get_BaseMessage(arg.basetype)
            if base:
                all_types.add(base)
        base = get_BaseMessage(return_type.basetype)
        if base:
            all_types.add(base)

    all_blocks: List[Block] = []

    for typ in all_types:
        blocks = cls_to_blocks(typ)
        all_blocks.extend(blocks)

    return all_blocks

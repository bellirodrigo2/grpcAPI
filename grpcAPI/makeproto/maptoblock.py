from enum import Enum
from typing import List, Optional, Set

from grpcAPI.makeproto.block_models import Block
from grpcAPI.makeproto.makeblock import make_enumblock, make_msgblock
from grpcAPI.makeproto.protoobj.message import BaseMessage
from grpcAPI.mapclass import map_class_fields


def cls_map(
    tgt: type[BaseMessage],
    visited: Optional[Set[Block]] = None,
) -> Set[BaseMessage]:

    if visited is None:
        visited: Set[BaseMessage] = set()

    if any(b.__name__ == tgt.__name__ for b in visited):
        return visited

    if issubclass(tgt, Enum) or issubclass(tgt, BaseMessage):
        visited.add(tgt)

        args = map_class_fields(tgt, False)

        for arg in args:
            if arg.istype(BaseMessage):
                msgs = cls_map(arg.basetype, visited)
                visited.update(msgs)
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

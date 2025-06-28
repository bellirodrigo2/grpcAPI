from typing import Any, Callable, List, Optional, Set, Type, Union

from typemapping import map_func_args, map_model_fields

from grpcAPI.types import BaseEnum, BaseMessage, get_BaseMessage


def cls_map(
    tgt: Type[BaseMessage],
    visited: Optional[Set[type[BaseMessage]]] = None,
) -> Set[type[BaseMessage]]:

    if visited is None:
        visited = set()

    if tgt in visited:
        return visited

    if issubclass(tgt, BaseEnum) or issubclass(tgt, BaseMessage):
        visited.add(tgt)

        args = map_model_fields(tgt, False)

        for arg in args:
            if arg.istype(BaseMessage):
                msgs = cls_map(arg.basetype, visited)
                visited.update(msgs)
            elif arg.istype(BaseEnum):
                visited.add(arg.basetype)
    return visited


def map_service_classes(
    methods: List[Callable[..., Any]],
) -> Set[type[Union[BaseMessage, BaseEnum]]]:
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
    classes: Set[type[Union[BaseMessage, BaseEnum]]] = set()
    for typ in all_types:
        clss = cls_map(typ)
        classes.update(clss)
    return classes

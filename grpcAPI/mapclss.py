from typing import Any, Callable, List, Optional, Set, Type, Union

from typemapping import map_model_fields

from grpcAPI.proto_inject import extract_request, get_return_type
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
        types = extract_request(method)
        method_types: Set[type] = set(types)

        if len(method_types) != 1:
            raise TypeError(
                f'Function "{method.__name__}" has multiple requests: "{list(method_types)}"'
            )
        return_type = get_return_type(method)
        base = get_BaseMessage(return_type)
        if base is None:
            raise TypeError(
                f'Function "{method.__name__}" has an invalid return type: "{return_type}"'
            )
        if base:
            method_types.add(base)
        all_types.update(method_types)
    classes: Set[type[Union[BaseMessage, BaseEnum]]] = set()
    for typ in all_types:
        clss = cls_map(typ)
        classes.update(clss)
    return classes

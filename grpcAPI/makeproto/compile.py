from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, List, Set, Tuple, Union

from grpcAPI.makeproto.makeblock import make_cls_block, make_service
from grpcAPI.makeproto.protoblock import Block
from grpcAPI.types import BaseMessage, ProtoOption, _NoPackage


@dataclass
class ServiceCompilerPack:
    servicename: str
    methods: List[Tuple[Callable[..., Any], str, ProtoOption]]
    description: str
    options: ProtoOption


@dataclass
class ModuleCompilerPack:
    package: Union[str, _NoPackage]
    protofile: str
    objects: Set[type[Union[BaseMessage, Enum]]]
    services: List[ServiceCompilerPack]
    description: str
    options: ProtoOption
    ignore_instance: List[type[Any]]


def map_to_blocks(module: ModuleCompilerPack) -> Tuple[str, ProtoOption, List[Block]]:

    blocks = [make_cls_block(cls) for cls in module.objects]

    for service in module.services:
        servblock = make_service(
            servicename=service.servicename,
            protofile=module.protofile,
            package=module.package,
            methods=service.methods,
            description=service.description,
            options=service.options,
            ignore_instance=module.ignore_instance,
        )
        blocks.append(servblock)

    return (module.description, module.options, blocks)

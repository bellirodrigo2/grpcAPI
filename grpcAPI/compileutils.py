from collections import defaultdict
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

from grpcAPI.app import App, Module
from grpcAPI.makeproto import ModuleCompilerPack, ServiceCompilerPack
from grpcAPI.typemapping import map_class_fields, map_func_args
from grpcAPI.types import BaseMessage, _NoPackage, get_BaseMessage


def make_compiler_entry(
    app: App, ignore_instance: List[type[Any]]
) -> Dict[str, List[ModuleCompilerPack]]:

    compilerpacks: Dict[str, List[ModuleCompilerPack]] = defaultdict(list)
    for package in app._packages.values():
        for module in package:
            objects = map_module_cls(module)
            services = map_module_service(module)

            modulecompilerpack = ModuleCompilerPack(
                package=module.packname,
                protofile=module.modname,
                objects=objects,
                services=services,
                description=module.description,
                options=module.options,
                ignore_instance=ignore_instance,
            )
            compilerpacks[package.packname].append(modulecompilerpack)
    return compilerpacks


def make_modules_set(
    packs: Dict[str, List[ModuleCompilerPack]],
) -> Set[Tuple[Union[_NoPackage, str], str]]:
    global_modules: Set[Tuple[Union[_NoPackage, str], str]] = set()
    for modulelist in packs.values():
        for module in modulelist:
            global_modules.add((module.package, module.protofile))
    return global_modules


def map_module_cls(mod: Module) -> Set[type[Union[BaseMessage, Enum]]]:

    clss: Set[type[Union[BaseMessage, Enum]]] = set()
    for servicepack in mod:
        funcs = [pack.method for pack in servicepack.methods]
        msgs_enums = map_service_classes(methods=funcs)
        clss.update(msgs_enums)
    return clss


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


def map_service_classes(
    methods: List[Callable[..., Any]],
) -> Set[type[Union[BaseMessage, Enum]]]:
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

    classes: Set[type[Union[BaseMessage, Enum]]] = set()
    for typ in all_types:
        clss = cls_map(typ)
        classes.update(clss)
    return classes


def map_module_service(mod: Module) -> List[ServiceCompilerPack]:
    servicecompilerpacks: List[ServiceCompilerPack] = []
    for servicepack in mod:
        servicecompiler = ServiceCompilerPack(
            servicename=servicepack.servname,
            methods=[
                (method.method, method.description, method.options)
                for method in servicepack.methods
            ],
            description=servicepack.description,
            options=servicepack.options,
        )
        servicecompilerpacks.append(servicecompiler)
    return servicecompilerpacks

from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Set, Tuple, Union

from grpcAPI.makeproto.compiler.compiler import CompilerContext, CompilerPass
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


class CompilationError(Exception):
    def __init__(self, contexts: List[CompilerContext]) -> None:
        self.contexts = contexts
        self.total_errors = sum(len(ctx) for ctx in contexts)
        super().__init__(
            f"Compilation failed with {self.total_errors} errors across {len(self.contexts)} packages."
        )


def modules_to_list_block(packs: List[ModuleCompilerPack]) -> List[Block]:
    return []


def make_execution_list(
    compilerpacks: List[ModuleCompilerPack],
    settings: Dict[str, Any],
) -> List[Tuple[List[Block], CompilerContext]]:

    blocks = modules_to_list_block(compilerpacks)
    for module in compilerpacks:
        # criar os templates aqui
        pass
    ctx = CompilerContext(
        # PRECISA CHECAR SE O PACK EH VAZIO ???
        name=compilerpacks[0].package,  # transformar NO_PACKAGE para str ??????
        # ADICIONAR AQUI UM TEMPLATE POR MODULE, PARA OS SETTERS USAREM
        # LISTA DE DESCRIPTION E OPTIONS POR MODULE
        state={},  # {"globalpacks": global_modules},
        settings=settings,
    )
    return (blocks, ctx)


def compile_packs(
    compilerpacks: Dict[str, List[ModuleCompilerPack]],
    settings: Dict[str, Any],
    passes: List[List[CompilerPass]],
) -> None:
    # global_modules = [(mcp.package, mcp.protofile) for mcp in compilerpacks]

    for pack in compilerpacks.values():
        execution_list = make_execution_list(pack, settings)
        for compilerpass in passes:
            run_compiler_passes(execution_list, compilerpass)


def run_compiler_passes(
    packs: List[Tuple[List[Block], CompilerContext]],
    compilerpass: List[CompilerPass],
) -> None:
    ctxs = [tup[1] for tup in packs]
    for cpass in compilerpass:
        for block, ctx in packs:
            cpass.execute(block, ctx)

        total_errors = sum(len(ctx) for ctx in ctxs)
        if total_errors > 0:
            raise CompilationError(ctxs)


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

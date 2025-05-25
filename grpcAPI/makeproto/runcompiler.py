from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Set, Tuple, Union

from grpcAPI.makeproto.compiler import CompilerContext, CompilerPass
from grpcAPI.makeproto.makeblock import make_cls_block, make_service
from grpcAPI.makeproto.protoblock import Block
from grpcAPI.makeproto.render.render import render_block, render_protofile
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
        state={},
        settings=settings,
    )
    return (blocks, ctx)


@dataclass
class ModuleTemplate:
    package: str
    imports: List[str] = field(default_factory=list[str])
    options: List[str] = field(default_factory=list[str])
    fields: List[str] = field(default_factory=list[str])
    blocks: List[Block] = field(default_factory=list[Block])
    version: int = 3

    def render(self) -> str:

        for block in self.blocks:
            render_dict = block.get_render_dict()
            block_str = self.render_block(render_dict)
            self.fields.append(block_str)

        del self.blocks

        return self.render_protofile(asdict(self))

    @property
    def render_block(self) -> Callable[[Dict[str, Any]], str]:
        return render_block

    @property
    def render_protofile(Self) -> Callable[[Dict[str, Any]], str]:
        return render_protofile


def compile_packs(
    compilerpacks: Dict[str, List[ModuleCompilerPack]],
    settings: Dict[str, Any],
    passes: List[List[CompilerPass]],
) -> None:
    # VER SE PRECISA MESMO DE DICT
    for packname, modules in compilerpacks.items():
        state = {}
        blocks: List[Block] = []
        for module in modules:
            # ADICIONAR IMPORTS E OPTIONS NOS SETTER AQUI NO MODULE
            modtemplate = ModuleTemplate(package=packname)
            state[module.protofile] = modtemplate
            # CRIAR OS BLOCKS
            # ADICIONAR A BLOCKS

        ctx = CompilerContext(name=packname, settings=settings, state=state)

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

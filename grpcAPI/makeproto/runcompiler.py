from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Set, Tuple, Union

from grpcAPI.makeproto.compiler import CompilerContext, CompilerPass
from grpcAPI.makeproto.makeblock import make_cls_block, make_service
from grpcAPI.makeproto.protoblock import Block
from grpcAPI.makeproto.render.render import render_block, render_protofile
from grpcAPI.types import BaseMessage, IModule, ProtoOption, _NoPackage


class CompilationError(Exception):
    def __init__(self, contexts: List[CompilerContext]) -> None:
        self.contexts = contexts
        self.total_errors = sum(len(ctx) for ctx in contexts)
        super().__init__(
            f"Compilation failed with {self.total_errors} errors across {len(self.contexts)} packages."
        )


@dataclass
class ModuleTemplate:
    package: str
    blocks: List[Block]
    imports: List[str] = field(default_factory=list[str])
    options: List[str] = field(default_factory=list[str])
    fields: List[str] = field(default_factory=list[str])
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


def module_to_list_block(
    module: IModule, ignore_instance: List[type[Any]]
) -> List[Block]:
    blocks = [make_cls_block(bt) for bt in module.objects]
    serviceblocks = [
        make_service(service, ignore_instance) for service in module.services
    ]
    return blocks + serviceblocks


def compile_packs(
    compilerpacks: Dict[str, List[IModule]],
    settings: Dict[str, Any],
    passes: List[List[CompilerPass]],
    ignore_instance: List[type[Any]],
) -> None:

    executionlist: List[Tuple[List[Block], CompilerContext]] = []
    allmodules: List[ModuleTemplate] = []
    for packname, modules in compilerpacks.items():
        state: Dict[str, ModuleTemplate] = {}
        blocks: List[Block] = []
        for module in modules:
            modblocks = module_to_list_block(module, ignore_instance)
            module_template = ModuleTemplate(package=packname, blocks=modblocks)
            state[module.name] = module_template
            allmodules.append(module_template)
            blocks.extend(modblocks)
        ctx = CompilerContext(name=packname, settings=settings, state=state)
        executionlist.append((blocks, ctx))

    for compilerpass in passes:
        run_compiler_passes(executionlist, compilerpass)

    # aqui allmodules esta pronto pra render


def run_compiler_passes(
    packs: List[Tuple[List[Block], CompilerContext]],
    compilerpass: List[CompilerPass],
) -> None:
    ctxs = [ctx for _, ctx in packs]
    for cpass in compilerpass:
        for block, ctx in packs:
            cpass.execute(block, ctx)

        total_errors = sum(len(ctx) for ctx in ctxs)
        if total_errors > 0:
            raise CompilationError(ctxs)

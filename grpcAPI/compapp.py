from typing import Any, Dict, List, Optional, Set, Tuple

from grpcAPI.app import App, Package, map_package_block
from grpcAPI.makeproto.compiler.compiler import CompilerContext, CompilerPass
from grpcAPI.makeproto.compiler.setters.imports import ImportsSetter
from grpcAPI.makeproto.compiler.setters.index import IndexSetter
from grpcAPI.makeproto.compiler.setters.info import DescriptionSetter, OptionsSetter
from grpcAPI.makeproto.compiler.setters.name import NameSetter
from grpcAPI.makeproto.compiler.setters.type import TypeSetter
from grpcAPI.makeproto.compiler.validators.blockstructure import BlockStructureValidator
from grpcAPI.makeproto.compiler.validators.index import IndexValidator
from grpcAPI.makeproto.compiler.validators.info import (
    DescriptionValidator,
    OneOfValidator,
    OptionsValidator,
)
from grpcAPI.makeproto.compiler.validators.name import (
    BlockNameValidator,
    FieldNameValidator,
)
from grpcAPI.makeproto.compiler.validators.type import TypeValidator
from grpcAPI.makeproto.protoblock import Block


class CompilationError(Exception):
    def __init__(self, contexts: List[CompilerContext]) -> None:
        self.contexts = contexts
        self.total_errors = sum(len(ctx) for ctx in contexts)
        super().__init__(
            f"Compilation failed with {self.total_errors} errors across {len(self.contexts)} packages."
        )


def make_state(packages: List[Package]) -> Dict[str, Any]:
    packset: Set[Tuple[str, str]] = set()
    for pack in packages:
        for mod in pack:
            packset.add((pack.packname, mod.modname))
    return {"_packages": packset}


def make_execution_tuple(
    packages: List[Package],
    settings: Dict[str, Any],
    ignore_instance: List[type[Any]],
) -> List[Tuple[List[Block], CompilerContext]]:
    tuples: List[Tuple[List[Block], CompilerContext]] = []
    state = make_state(packages)
    for pack in packages:
        ctx = CompilerContext(name=pack.packname, state=state, settings=settings)
        blocks = map_package_block(pack, ignore_instance)
        tuples.append((blocks, ctx))
    return tuples


def prepare_packages(
    app: App,
    settings: Optional[Dict[str, Any]] = None,
    ignore_instance: Optional[List[type[Any]]] = None,
) -> List[Tuple[List[Block], CompilerContext]]:
    settings = settings or {}
    ignore_instance = ignore_instance or []

    packages: List[Package] = list(app.packages.values())
    return make_execution_tuple(packages, settings, ignore_instance)


def run_compiler_passes(
    execution_list: List[Tuple[List[Block], CompilerContext]],
    passes_list: List[List[CompilerPass]],
) -> List[List[Block]]:

    ctxs = [tup[1] for tup in execution_list]
    for passes in passes_list:
        for block, ctx in execution_list:
            for pass_ in passes:
                pass_.execute(block, ctx)

        total_errors = sum(len(ctx) for ctx in ctxs)
        if total_errors > 0:
            raise CompilationError(ctxs)

    return [tup[0] for tup in execution_list]


validators: List[CompilerPass] = [
    BlockStructureValidator,
    TypeValidator,
    BlockNameValidator,
    FieldNameValidator,
    IndexValidator,
    OptionsValidator,
    DescriptionValidator,
    OneOfValidator,
]  # type: ignore

setters: List[CompilerPass] = [
    TypeSetter,
    NameSetter,
    IndexSetter,
    ImportsSetter,
    DescriptionSetter,
    OptionsSetter,
]

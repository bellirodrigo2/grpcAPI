import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

from grpcAPI.makeproto.compiler import CompilerContext, CompilerPass
from grpcAPI.makeproto.makeblock import make_cls_block, make_service
from grpcAPI.makeproto.protoblock import Block
from grpcAPI.makeproto.render.render import BaseModuleTemplate
from grpcAPI.makeproto.setters.imports import ImportsSetter
from grpcAPI.makeproto.setters.index import IndexSetter
from grpcAPI.makeproto.setters.info import (
    DescriptionSetter,
    OptionsSetter,
    ReservedSetter,
)
from grpcAPI.makeproto.setters.name import NameSetter
from grpcAPI.makeproto.setters.type import TypeSetter
from grpcAPI.makeproto.validators.blockstructure import BlockStructureValidator
from grpcAPI.makeproto.validators.custommethod import CustomPass
from grpcAPI.makeproto.validators.imports import ImportsValidator
from grpcAPI.makeproto.validators.index import IndexValidator
from grpcAPI.makeproto.validators.info import (
    DescriptionValidator,
    OneOfValidator,
    OptionsValidator,
    ReservedValidator,
)
from grpcAPI.makeproto.validators.name import BlockNameValidator, FieldNameValidator
from grpcAPI.makeproto.validators.type import TypeValidator
from grpcAPI.types import IPackage, _NoPackage


class CompilationError(Exception):
    def __init__(self, contexts: List[CompilerContext]) -> None:
        self.contexts = contexts
        self.total_errors = sum(len(ctx) for ctx in contexts)
        super().__init__(
            f"Compilation failed with {self.total_errors} errors across {len(self.contexts)} packages."
        )


@dataclass
class ModuleTemplate(BaseModuleTemplate):
    def __init__(self, blocks: List[Block], **kwargs: Any):
        super().__init__(**kwargs)
        self.blocks = blocks

    def render(self) -> str:
        for block in self.blocks:
            self.add_field(block.get_render_dict())
        str_file = super().render()
        str_file = re.sub(r"^[ \t]*\n", "", str_file, flags=re.MULTILINE)
        # str_file = str_file.replace("\n\n", "\n").replace("\n ", "\n")
        return str_file


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


def make_validators(
    custompassmethod: Callable[[Any], List[str]] = lambda x: [],
) -> List[CompilerPass]:

    custompass = CustomPass(visitmethod=custompassmethod)

    return [
        BlockStructureValidator(),
        TypeValidator(),
        BlockNameValidator(),
        FieldNameValidator(),
        IndexValidator(),
        OptionsValidator(),
        DescriptionValidator(),
        OneOfValidator(),
        ReservedValidator(),
        custompass,
    ]


def make_setters(
    settings: Dict[str, Any],
) -> List[CompilerPass]:

    MAXCHAR_PER_LINE = settings.get("maxchar_per_line", 80)
    ALWAYS_FORMAT = settings.get("always_format", True)
    return [
        TypeSetter(),
        NameSetter(),
        IndexSetter(),
        ImportsSetter(),
        DescriptionSetter(MAXCHAR_PER_LINE, ALWAYS_FORMAT),
        OptionsSetter(),
        ReservedSetter(),
    ]


def make_imports_validator(
    packlist: List[IPackage],
) -> ImportsValidator:
    global_modules: Set[Tuple[Union[str, _NoPackage], str]] = {
        (module.package, module.name) for pack in packlist for module in pack.modules
    }
    return ImportsValidator(packset=global_modules)


def extract_cls_blocks(
    packlist: List[IPackage],
) -> Dict[Tuple[Union[str, _NoPackage], str], List[Block]]:

    block_dict: Dict[Tuple[Union[str, _NoPackage], str], List[Block]] = defaultdict(
        list
    )
    for package in packlist:
        for module in package.modules:
            blocks = [make_cls_block(bt) for bt in module.objects]
            for block in blocks:
                block_dict[(block.package, block.protofile)].append(block)
    return block_dict


def make_execution_list(
    packlist: List[IPackage],
    settings: Dict[str, Any],
    version: int = 3,
    getargs: Optional[Callable[[Callable[..., Any]], List[Optional[type[Any]]]]] = None,
) -> Tuple[List[ModuleTemplate], List[Tuple[List[Block], CompilerContext]]]:
    executionlist = []
    allmodules = []
    cls_blocks_dict = extract_cls_blocks(packlist)
    for package in packlist:
        state: Dict[str, ModuleTemplate] = {}
        # ADICIONAR OS FILE LEVEL REPORT AQUI
        blocks = []
        for module in package.modules:
            service_blocks = [
                make_service(service, getargs) for service in module.services
            ]
            cls_blocks = cls_blocks_dict.get((package.name, module.name), [])
            modblocks = cls_blocks + service_blocks
            module_template = ModuleTemplate(
                modulename=module.name,
                version=version,
                package=package.name,
                blocks=modblocks,
                description=module.description or "",
                fields=[],
                imports=set([]),
                options=[],
            )
            state[module.name] = module_template
            allmodules.append(module_template)
            blocks.extend(modblocks)
        ctx = CompilerContext(name=package.name, settings=settings, state=state)
        executionlist.append((blocks, ctx))
    return allmodules, executionlist


def make_protos(
    packlist: List[IPackage],
    settings: Dict[str, Any],
    custompassmethod: Callable[[Any], List[str]] = lambda x: [],
    convert_arg: Optional[Callable[[Callable[..., Any]], List[type[Any]]]] = None,
) -> Optional[Dict[str, Dict[str, str]]]:

    imports_validator = make_imports_validator(packlist)
    validators = make_validators(custompassmethod)
    validators.append(imports_validator)

    VERSION = settings.get("version", 3)

    allmodules, executionlist = make_execution_list(
        packlist, settings, version=VERSION, getargs=convert_arg
    )

    setters = make_setters(settings)
    passes: List[List[CompilerPass]] = [validators, setters]

    try:
        for compilerpass in passes:
            run_compiler_passes(executionlist, compilerpass)
    except CompilationError as e:
        for ctx in e.contexts:
            if ctx.has_errors():
                ctx.show()
        return None

    proto_files: Dict[str, Dict[str, str]] = defaultdict(dict)
    for template in allmodules:
        rendered = template.render()
        package = template.package if isinstance(template.package, str) else "NOPCKG"
        proto_files[package][template.modulename] = rendered

    return proto_files

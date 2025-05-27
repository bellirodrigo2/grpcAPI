import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

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
from grpcAPI.types import IModule, IPackage, _NoPackage


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
        return super().render()


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
    settings: Dict[str, Any],
) -> List[CompilerPass]:

    custompassmethod = settings.get("custompass", lambda x: [])
    custompass = CustomPass(visitmethod=custompassmethod)

    EXTRA_ARGS = settings.get("extra_args", [])

    return [
        BlockStructureValidator(),
        TypeValidator(EXTRA_ARGS),
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
    ignore_instance: List[type[Any]],
    version: int = 3,
) -> Tuple[List[ModuleTemplate], List[Tuple[List[Block], CompilerContext]]]:
    executionlist = []
    allmodules = []
    cls_blocks_dict = extract_cls_blocks(packlist)
    for package in packlist:
        state: Dict[str, ModuleTemplate] = {}
        blocks = []
        for module in package.modules:
            # modblocks = module_to_list_block(module, ignore_instance)
            service_blocks = [
                make_service(service, ignore_instance) for service in module.services
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
    ignore_instance: List[type[Any]],
) -> Optional[List[ModuleTemplate]]:

    imports_validator = make_imports_validator(packlist)
    validators = make_validators(settings)
    validators.append(imports_validator)

    VERSION = settings.get("version", 3)

    allmodules, executionlist = make_execution_list(
        packlist,
        settings,
        ignore_instance,
        version=VERSION,
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
        return
    return allmodules


def compile_packs(
    packlist: List[IPackage],
    settings: Dict[str, Any],
    version_mode: str,
    ignore_instance: List[type[Any]],
) -> None:

    allmodules = make_protos(
        packlist,
        settings,
        ignore_instance,
    )
    if allmodules is None:
        return

    if version_mode == "lint":
        print("[LINT] Compilation passed successfully. No files written.")
        return

    output_dir = Path(settings.get("output_dir", "grpcAPI/proto"))
    output_subdir = determine_output_subdir(output_dir, mode=version_mode)

    if output_subdir is not None:
        write_modules_to_files(allmodules, output_subdir)


def write_modules_to_files(
    modules: List[ModuleTemplate],
    output_dir: Path,
) -> None:
    for module in modules:
        package_path = output_dir / module.package
        package_path.mkdir(parents=True, exist_ok=True)

        filename = f"{module.modulename}.proto"
        file_path = package_path / filename

        proto_text = module.render()

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(proto_text)

        print(f"Wrote proto file: {file_path}")


def determine_output_subdir(
    output_dir: Path,
    mode: str = "new",
) -> Optional[Path]:
    if mode == "new":
        versions = []
        for child in output_dir.iterdir():
            if child.is_dir() and re.match(r"^V\d+$", child.name):
                version_num = int(child.name[1:])
                versions.append(version_num)
        next_version = max(versions, default=0) + 1
        target_dir = output_dir / f"V{next_version}"
        print(f"[INFO] Creating new version directory: {target_dir}")

    elif mode == "overwrite":
        versions = []
        for child in output_dir.iterdir():
            if child.is_dir() and re.match(r"^V\d+$", child.name):
                version_num = int(child.name[1:])
                versions.append(version_num)
        if not versions:
            raise ValueError("No existing version found to overwrite.")
        last_version = max(versions)
        target_dir = output_dir / f"V{last_version}"
        print(f"[INFO] Overwriting last version directory: {target_dir}")

    elif mode == "draft":
        target_dir = output_dir / "draft"
        print(f"[INFO] Using draft directory: {target_dir}")

    elif mode == "temporary":
        target_dir = output_dir / "tmp"
        print(f"[INFO] Using temporary directory: {target_dir}")

    elif mode == "lint":
        print(f"[INFO] Lint mode: no files will be written.")
        return None

    else:
        raise ValueError(f"Unknown mode: {mode}")

    target_dir.mkdir(parents=True, exist_ok=True)
    return target_dir

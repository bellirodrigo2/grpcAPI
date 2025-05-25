from typing import Any, Callable, Dict, List, Set, Tuple, Union

from grpcAPI.app import App
from grpcAPI.makeproto import (
    BlockNameValidator,
    BlockStructureValidator,
    CustomPass,
    DescriptionSetter,
    DescriptionValidator,
    FieldNameValidator,
    ImportsSetter,
    ImportsValidator,
    IndexSetter,
    IndexValidator,
    NameSetter,
    OneOfValidator,
    OptionsSetter,
    OptionsValidator,
    ReservedSetter,
    ReservedValidator,
    TypeSetter,
    TypeValidator,
    compile_packs,
)
from grpcAPI.types import Context
from grpcAPI.types.interfaces import IModule
from grpcAPI.types.message import _NoPackage

settings: Dict[str, Any] = {}


def placeholder(func: Callable[..., Any]) -> List[str]:
    return []


ctxinjectpass = CustomPass(visitmethod=placeholder)

# LER DE std_config.json em makeproto.compiler
# ler de makeproto.compiler

# NAMESETTER
# DEFAULT_CASE = NameTransformStrategy.NO_TRANSFORM
# **** precisa de um de para

# DescriptionSetter
MAXCHAR_PER_LINE = 80
ALWAYS_FORMAT = True

# TypeValidator
DEFAULT_EXTRA_ARGS = [Context]


validators = [
    BlockStructureValidator(),
    TypeValidator(DEFAULT_EXTRA_ARGS),
    BlockNameValidator(),
    FieldNameValidator(),
    IndexValidator(),
    OptionsValidator(),
    DescriptionValidator(),
    OneOfValidator(),
    ReservedValidator(),
    ctxinjectpass,
]  # type: ignore

setters = [
    TypeSetter(),
    NameSetter(),
    IndexSetter(),
    ImportsSetter(),
    DescriptionSetter(MAXCHAR_PER_LINE, ALWAYS_FORMAT),
    OptionsSetter(),
    ReservedSetter(),
]


def make_modules_set(
    packs: Dict[str, List[IModule]],
) -> Set[Tuple[Union[_NoPackage, str], str]]:
    global_modules: Set[Tuple[Union[_NoPackage, str], str]] = set()
    for modulelist in packs.values():
        for module in modulelist:
            global_modules.add((module.package, module.name))
    return global_modules


def compile(app: App, ignore_instance: List[type[Any]]) -> None:

    compilerpacks = {
        package.packname: package.modules for package in app._packages.values()
    }
    global_modules = make_modules_set(compilerpacks)
    importsvalidator = ImportsValidator(packset=global_modules)
    validators.append(importsvalidator)
    compile_packs(compilerpacks, settings, [validators, setters], ignore_instance: List[type[Any]])

from typing import Any, Callable, Dict, List

from grpcAPI.app import App
from grpcAPI.compileutils import make_compiler_entry, make_modules_set
from grpcAPI.makeproto import compile_packs
from grpcAPI.makeproto.compiler import (
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
)
from grpcAPI.types import Context

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


def compile(app: App, ignore_instance: List[type[Any]]) -> None:

    compilerpacks = make_compiler_entry(app, ignore_instance)
    global_modules = make_modules_set(compilerpacks)
    importsvalidator = ImportsValidator(packset=global_modules)
    validators.append(importsvalidator)
    compile_packs(compilerpacks, settings, [validators, setters])

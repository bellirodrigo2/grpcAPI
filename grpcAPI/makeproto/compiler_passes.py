from typing_extensions import Any, Callable, List, Tuple

from grpcAPI.makeproto.compiler import CompilerContext, CompilerPass
from grpcAPI.makeproto.format_comment import format_comment
from grpcAPI.makeproto.setters.comment import CommentSetter
from grpcAPI.makeproto.setters.imports import ImportsSetter
from grpcAPI.makeproto.setters.name import NameSetter
from grpcAPI.makeproto.setters.service import ServiceSetter
from grpcAPI.makeproto.setters.type import TypeSetter
from grpcAPI.makeproto.template import ServiceTemplate
from grpcAPI.makeproto.validators.comment import CommentsValidator
from grpcAPI.makeproto.validators.custommethod import CustomPass
from grpcAPI.makeproto.validators.imports import ImportsValidator
from grpcAPI.makeproto.validators.name import BlockNameValidator, FieldNameValidator
from grpcAPI.makeproto.validators.type import TypeValidator


class CompilationError(Exception):
    def __init__(self, contexts: List[CompilerContext]) -> None:
        self.contexts = contexts
        self.total_errors = sum(len(ctx) for ctx in contexts)
        super().__init__(
            f"Compilation failed with {self.total_errors} errors across {len(self.contexts)} packages."
        )


def run_compiler_passes(
    packs: List[Tuple[List[ServiceTemplate], CompilerContext]],
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
        TypeValidator(),
        BlockNameValidator(),
        ImportsValidator(),
        FieldNameValidator(),
        CommentsValidator(),
        custompass,
    ]


default_format = format_comment


def make_setters(
    name_normalizer: Callable[[str], str] = lambda x: x,
    format_comment: Callable[[str], str] = default_format,
) -> List[CompilerPass]:

    setters: List[CompilerPass] = [
        ServiceSetter(),
        TypeSetter(),
        NameSetter(name_normalizer),
        ImportsSetter(),
        CommentSetter(format_comment),
    ]
    return setters

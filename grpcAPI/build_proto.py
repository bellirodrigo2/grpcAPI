import sys

from typing_extensions import Any, AsyncIterator, Callable, Iterable, List, Mapping

from grpcAPI.app import APIService
from grpcAPI.ctxinject_proto import (
    func_signature_check,
    ignore_context_metadata,
    ignore_enum,
    protobuf_types_predicate,
)
from grpcAPI.datatypes import AsyncContext, Message, get_function_metadata
from grpcAPI.makeproto import IProtoPackage, compile_service
from grpcAPI.makeproto.compiler import CompilerContext


def validate_signature_pass(
    func: Callable[..., Any],
) -> List[str]:
    bynames = get_function_metadata(func)
    return func_signature_check(
        func,
        [Message, AsyncIterator[Message], AsyncContext],
        bynames or {},
        True,
        [protobuf_types_predicate, ignore_enum, ignore_context_metadata],
    )


class CompilerException(RuntimeError):

    def __init__(self, context: CompilerContext) -> None:
        super().__init__("Proto compilation failed")
        self.context = context


def make_protos(
    services: Mapping[str, List[APIService]], exit: bool = True
) -> Iterable[IProtoPackage]:

    proto_stream = compile_service(
        services=services,
        custompassmethod=validate_signature_pass,
        version=3,
    )
    if isinstance(proto_stream, CompilerContext):
        if exit:
            sys.exit(1)
        else:
            raise CompilerException(proto_stream)
    return proto_stream

import sys

from typing_extensions import Any, AsyncIterator, Callable, Iterable, List, Mapping

from grpcAPI.app import APIService
from grpcAPI.data_types import AsyncContext, Message, get_function_metadata
from grpcAPI.makeproto import IProtoPackage, compile_service
from grpcAPI.proto_ctxinject import (
    func_signature_check,
    ignore_context_metadata,
    ignore_enum,
    protobuf_types_predicate,
)


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


def make_protos(
    services: Mapping[str, List[APIService]],
) -> Iterable[IProtoPackage]:

    proto_stream = compile_service(
        services=services,
        custompassmethod=validate_signature_pass,
        version=3,
    )
    if not proto_stream:
        sys.exit(1)
    return proto_stream

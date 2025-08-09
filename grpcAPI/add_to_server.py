from collections.abc import AsyncIterator

import grpc
from typing_extensions import Any, Callable, Dict, Mapping, Tuple

from grpcAPI import ExceptionRegistry
from grpcAPI.make_method import make_method_async
from grpcAPI.makeproto import ILabeledMethod, IService
from grpcAPI.server import ServerWrapper


def add_to_server(
    service: IService,
    server: ServerWrapper,
    overrides: Dict[Callable[..., Any], Callable[..., Any]],
    exception_registry: ExceptionRegistry,
) -> Mapping[str, Callable[..., Any]]:

    rpc_method_handlers: Dict[str, Any] = {}
    methods: Dict[str, Callable[..., Any]] = {}
    for method in service.methods:
        key = method.name
        handler = get_handler(method)
        tgt_method = make_method_async(method, overrides, exception_registry)
        methods[key] = tgt_method
        req_des, resp_ser = get_deserializer_serializer(method)
        rpc_method_handlers[key] = handler(
            tgt_method,
            request_deserializer=req_des,
            response_serializer=resp_ser,
        )
    service_name = service.qual_name
    generic_handler = grpc.method_handlers_generic_handler(
        service_name, rpc_method_handlers
    )
    server.add_generic_rpc_handlers((generic_handler,))
    server.add_registered_method_handlers(service_name, rpc_method_handlers)

    return methods


def get_handler(method: ILabeledMethod) -> Callable[..., Any]:

    client_stream = method.request_types[0].origin is AsyncIterator
    server_stream = method.response_types.origin is AsyncIterator

    handlers: Dict[Tuple[bool, bool], Callable[..., Any]] = {
        (False, False): grpc.unary_unary_rpc_method_handler,
        (True, False): grpc.stream_unary_rpc_method_handler,
        (False, True): grpc.unary_stream_rpc_method_handler,
        (True, True): grpc.stream_stream_rpc_method_handler,
    }

    return handlers[(client_stream, server_stream)]


def get_deserializer_serializer(
    method: ILabeledMethod,
) -> Tuple[Callable[..., Any], Callable[..., Any]]:

    request_type = method.request_types[0].basetype
    response_type = method.response_types.basetype
    return (
        request_type.FromString,
        response_type.SerializeToString,
    )

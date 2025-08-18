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


from google.protobuf import descriptor_pb2, descriptor_pool


def register_fake_service(
    file_name: str, package: str, service_name: str, methods: list[tuple[str, str, str]]
):
    """
    Cria um FileDescriptorProto com um service e o registra no pool global.

    Args:
        file_name (str): nome do arquivo proto fictício (ex: "fake.proto")
        package (str): nome do package (ex: "mypackage")
        service_name (str): nome do service (ex: "MyService")
        methods (list[tuple[str,str,str]]): lista de métodos no formato
            (method_name, input_type, output_type)
            Ex: [("SayHello", ".mypackage.HelloRequest", ".mypackage.HelloReply")]
    """
    file_desc_proto = descriptor_pb2.FileDescriptorProto()
    file_desc_proto.name = file_name
    file_desc_proto.package = package

    # Cria service e métodos
    service = file_desc_proto.service.add()
    service.name = service_name

    for method_name, input_type, output_type in methods:
        rpc = service.method.add()
        rpc.name = method_name
        rpc.input_type = input_type
        rpc.output_type = output_type

    # Registra no pool global
    pool = descriptor_pool.Default()
    pool.Add(file_desc_proto)

    return file_desc_proto

from google.protobuf.message import Message

MESSAGE_TYPE = Message

from ctxinject.model import Depends as InnerDepends
from ctxinject.model import ModelFieldInject

DEPENDS_TYPE = InnerDepends
MODELFIELDINJECT_TYPE = ModelFieldInject

from grpcAPI.grpcio_adaptor.get_class_metadata import (
    get_package,
    get_protofile_relative_path,
)

GET_PACKAGE = get_package
GET_PROTOFILE_PATH = get_protofile_relative_path

from grpcAPI.grpcio_adaptor.make_method import make_method_async

MAKE_METHOD_ASYNC = make_method_async

from grpcAPI.grpcio_adaptor.makeproto_pass import validate_signature_pass

VALIDATE_SIGNATURE_PASS = validate_signature_pass

from grpcAPI.grpcio_adaptor.imodule import GrpcioServiceModule

SERVICE_MODULE = GrpcioServiceModule

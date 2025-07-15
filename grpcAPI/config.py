from pathlib import Path

from google.protobuf.message import Message

MESSAGE_TYPE = Message

from grpcAPI.grpcio_adaptor.get_class_metadata import (
    get_package,
    get_protofile_relative_path,
)

GET_PACKAGE = get_package
GET_PROTOFILE_PATH = get_protofile_relative_path

from grpcAPI.grpcio_adaptor.makeproto_pass import validate_signature_pass

VALIDATE_SIGNATURE_PASS = validate_signature_pass

from grpcAPI.grpcio_adaptor.inject_validation import StdValidator

STD_VALIDATOR = StdValidator

from grpcAPI.grpcio_adaptor.protoc_compile import compile_protoc

COMPILE_PROTO = compile_protoc

from grpcAPI.grpcio_adaptor.grpcio_module import GrpcioServiceModule

SERVICE_MODULE = GrpcioServiceModule

from grpcAPI.grpcio_adaptor.async_server import grpcaio_server_factory

SERVER_FACTORY = grpcaio_server_factory

plugin_path = Path("./grpcAPI/grpcio_adaptor/server_plugins")

# LOGGER
import json
import logging
import logging.config

logger_path = Path("./grpcAPI/settings/config.json")
with logger_path.open("r", encoding="utf-8") as f:
    config = json.load(f)
    LOGGING_CONFIG = config.get("logger")
    logging.config.dictConfig(LOGGING_CONFIG)
logging.getLogger().setLevel(logging.ERROR)

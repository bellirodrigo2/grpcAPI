from pathlib import Path

from typing_extensions import Any

from grpcAPI.protoc_compile import compile_protoc

COMPILE_PROTO = compile_protoc

plugin_path = Path("./grpcAPI/grpcio_adaptor/server_plugins")

from grpc import aio

type Middleware = aio.ServerInterceptor[Any, Any]

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

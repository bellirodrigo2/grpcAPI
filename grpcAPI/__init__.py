__all__ = ["ErrorCode", "AsyncContext", "ExceptionRegistry", "__version__"]
from grpc import StatusCode as ErrorCode
from typing_extensions import Callable, Dict, Type

from grpcAPI.data_types import AsyncContext
from grpcAPI._version import __version__

ExceptionRegistry = Dict[Type[Exception], Callable[[Exception, AsyncContext], None]]

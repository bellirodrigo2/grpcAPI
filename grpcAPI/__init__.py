__all__ = ["ErrorCode", "AsyncContext", "ExceptionRegistry"]
from grpc import StatusCode as ErrorCode
from typing_extensions import Callable, Dict, Type

from grpcAPI.data_types import AsyncContext

ExceptionRegistry = Dict[Type[Exception], Callable[[Exception, AsyncContext], None]]

from grpc import StatusCode as ErrorCode
from typing_extensions import Callable, Dict, Type

from grpcAPI.types import AsyncContext

ExceptionRegistry = Dict[Type[Exception], Callable[[Exception, AsyncContext], None]]

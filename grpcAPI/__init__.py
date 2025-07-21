from typing import Callable, Dict, Tuple, Type

from grpc import StatusCode as ErrorCode

ExceptionRegistry = Dict[Type[Exception], Callable[[Exception], Tuple[ErrorCode, str]]]

from enum import Enum
from typing import Callable, Dict, Tuple, Type

from grpc import StatusCode

type ExceptionRegistry = Dict[
    Type[Exception], Callable[[Exception], Tuple[ErrorCode, str]]
]


class ErrorCode(Enum):
    OK = StatusCode.OK
    CANCELLED = StatusCode.CANCELLED
    UNKNOWN = StatusCode.UNKNOWN
    INVALID_ARGUMENT = StatusCode.INVALID_ARGUMENT
    DEADLINE_EXCEEDED = StatusCode.DEADLINE_EXCEEDED
    NOT_FOUND = StatusCode.NOT_FOUND
    ALREADY_EXISTS = StatusCode.ALREADY_EXISTS
    PERMISSION_DENIED = StatusCode.PERMISSION_DENIED
    RESOURCE_EXHAUSTED = StatusCode.RESOURCE_EXHAUSTED
    FAILED_PRECONDITION = StatusCode.FAILED_PRECONDITION
    ABORTED = StatusCode.ABORTED
    OUT_OF_RANGE = StatusCode.OUT_OF_RANGE
    UNIMPLEMENTED = StatusCode.UNIMPLEMENTED
    INTERNAL = StatusCode.INTERNAL
    UNAVAILABLE = StatusCode.UNAVAILABLE
    DATA_LOSS = StatusCode.DATA_LOSS
    UNAUTHENTICATED = StatusCode.UNAUTHENTICATED

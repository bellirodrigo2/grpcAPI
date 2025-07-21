from datetime import date, datetime, time
from typing import Callable, Tuple, Type

from ctxinject.validate import (
    constrained_bytejson,
    constrained_date,
    constrained_datetime,
    constrained_json,
    constrained_time,
)
from ctxinject.validate import inject_validation as ctxinject_inject_validation
from google.protobuf.struct_pb2 import ListValue, Struct
from google.protobuf.timestamp_pb2 import Timestamp
from makeproto import IService
from typing_extensions import Any, Callable, Dict, List, Tuple, Type

from grpcAPI.makeproto_pass import inject_typing
from grpcAPI.process_service import ProcessService


def convert_timestamp(
    value: Timestamp,
    **kwargs: Any,
) -> datetime:

    ts = value.ToDatetime()
    start = kwargs.get("start", None)
    end = kwargs.get("end", None)

    if start is not None and ts < start:
        raise ValueError(...)
    if end is not None and ts > end:
        raise ValueError(...)

    return ts


common_argproc: Dict[Tuple[type[Any], Type[Any]], Callable[..., Any]] = {
    (str, date): constrained_date,
    (str, time): constrained_time,
    (str, datetime): constrained_datetime,
    (str, dict): constrained_json,
    (bytes, dict): constrained_bytejson,
    (Timestamp, datetime): convert_timestamp,
    (Struct, Dict[str, Any]): lambda x: x,
    (ListValue, List[Any]): lambda x: x,
}


class BaseValidator(ProcessService):

    def __init__(
        self, argproc: Dict[Tuple[Type[Any], Type[Any]], Callable[..., Any]]
    ) -> None:
        self.argproc = {**argproc, **common_argproc}

    @property
    def casting_list(self) -> List[Tuple[Type[Any], Type[Any]]]:
        return list(self.argproc.keys())

    def __call__(self, service: IService) -> None:
        for method in service.methods:
            self.inject_validation(method.method)

    def inject_validation(self, func: Callable[..., Any]) -> None:
        inject_typing(func)
        ctxinject_inject_validation(func, self.argproc)

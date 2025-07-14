from datetime import datetime

from ctxinject.validate import arg_proc
from ctxinject.validate import inject_validation as ctinject_inject_validation
from google.protobuf.json_format import MessageToDict
from google.protobuf.struct_pb2 import ListValue, Struct
from google.protobuf.timestamp_pb2 import Timestamp
from typing_extensions import Any, Callable, Dict, List, Tuple, Type

from grpcAPI.interfaces import Validator

argproc = arg_proc


class StdValidator(Validator):

    def __init__(
        self,
    ) -> None:
        self.argproc = argproc

    @property
    def casting_list(self) -> List[Tuple[Type[Any], Type[Any]]]:
        return list(self.argproc.keys())

    def inject_validation(self, func: Callable[..., Any]) -> None:
        ctinject_inject_validation(func, self.argproc)


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


argproc[(Timestamp, datetime)] = convert_timestamp


def convert_struct(
    value: Struct,
    **kwargs: Any,
) -> Dict[str, Any]:
    d = MessageToDict(value)

    min_items = kwargs.get("min_items", None)
    max_items = kwargs.get("max_items", None)

    if min_items is not None and len(d) < min_items:
        raise ValueError(...)
    if max_items is not None and len(d) > max_items:
        raise ValueError(...)
    return d


argproc[(Struct, dict)] = convert_struct


def convert_list(
    value: ListValue,
    **kwargs: Any,
) -> List[Any]:
    temp = MessageToDict(value)

    lst: List[Any] = temp["values"]

    min_items = kwargs.get("min_items", None)
    max_items = kwargs.get("max_items", None)

    if min_items is not None and len(lst) < min_items:
        raise ValueError(...)
    if max_items is not None and len(lst) > max_items:
        raise ValueError(...)
    return lst


argproc[(Struct, list)] = convert_list

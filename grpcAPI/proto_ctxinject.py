__all__ = [
    "protobuf_types_predicate",
    "DependsInject",
    "ModelFieldInject",
    "func_signature_check",
    "ignore_enum",
    "get_mapped_ctx",
    "resolve_mapped_ctx",
]
from datetime import datetime
from typing import Any, Callable, Dict, Hashable, Optional, Tuple, Type

from ctxinject import (
    DependsInject,
    ModelFieldInject,
    func_signature_check,
    get_mapped_ctx,
    resolve_mapped_ctx,
)
from ctxinject.validation import arg_proc, constrained_dict, constrained_list
from google.protobuf.internal.enum_type_wrapper import EnumTypeWrapper
from google.protobuf.struct_pb2 import ListValue, Struct
from google.protobuf.timestamp_pb2 import Timestamp
from typemapping import get_args, get_equivalent_origin, is_equivalent_origin


def protobuf_types_predicate(
    _: ModelFieldInject,
    modeltype: Type[Any],
    basetype: Type[Any],
) -> bool:
    return is_equivalent_origin(modeltype, basetype)


def ignore_enum(
    _: ModelFieldInject,
    modeltype: Type[Any],
    basetype: Type[Any],
) -> bool:

    def destruct_enum(btype: Type[Any]) -> Tuple[Optional[Type[Any]], bool]:
        eq_origin = get_equivalent_origin(btype)
        args = get_args(btype)
        if isinstance(eq_origin, EnumTypeWrapper):
            eq_origin = None
        if eq_origin is dict:
            tgttype = args[1]
        elif eq_origin is list:
            tgttype = args[0]
        else:
            tgttype = btype

        return eq_origin, isinstance(tgttype, EnumTypeWrapper)

    return bool(destruct_enum(modeltype) == destruct_enum(basetype))


def convert_timestamp(
    value: Timestamp,
    **kwargs: Any,
) -> datetime:

    ts = value.ToDatetime()
    start = kwargs.get("start", None)
    end = kwargs.get("end", None)

    if start is not None and ts < start:
        raise ValueError(f"Datetime value must be on or after {start}")
    if end is not None and ts > end:
        raise ValueError(f"Datetime value must be on or before {end}")

    return ts


protobuf_converts: Dict[Tuple[Hashable, Hashable], Callable[..., Any]] = {
    (Timestamp, datetime): convert_timestamp,
    (Struct, Struct): constrained_dict,
    (ListValue, ListValue): constrained_list,
}

arg_proc.update(protobuf_converts)

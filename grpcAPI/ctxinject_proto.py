__all__ = [
    "protobuf_types_predicate",
    "DependsInject",
    "ModelFieldInject",
    "func_signature_check",
    "ignore_enum",
    "get_mapped_ctx",
    "resolve_mapped_ctx",
    "CastType",
    "Validation",
]
from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import Any, Callable, Dict, Hashable, List, Optional, Tuple, Type

from ctxinject import (
    DependsInject,
    ModelFieldInject,
    func_signature_check,
    get_mapped_ctx,
    resolve_mapped_ctx,
)
from ctxinject.model import CastType, Validation
from ctxinject.validation import arg_proc, constrained_list
from google.protobuf.internal.enum_type_wrapper import EnumTypeWrapper
from google.protobuf.struct_pb2 import ListValue, Struct
from google.protobuf.timestamp_pb2 import Timestamp
from typemapping import (
    get_args,
    get_equivalent_origin,
    get_origin,
    is_equivalent_origin,
)


class ProtobufEnum(int):
    pass


def protobuf_types_predicate(
    modeltype: Type[Any],
    basetype: Type[Any],
) -> bool:
    return is_equivalent_origin(modeltype, basetype)


def ignore_context_metadata(
    modeltype: Type[Any],
    basetype: Type[Any],
) -> bool:
    base_origin = get_origin(basetype)
    base_args = get_args(basetype)

    model_origin = get_origin(modeltype)
    model_args = get_args(modeltype)

    if (
        base_origin is Mapping
        and base_args == (str, str)
        and model_origin is Sequence
        and model_args == (Tuple[str, str],)
    ):
        return True
    return False


def ignore_enum(
    modeltype: Type[Any],
    basetype: Type[Any],
) -> bool:

    def destruct_enum(btype: Type[Any]) -> Tuple[Optional[Type[Any]], bool]:
        eq_origin = get_equivalent_origin(btype)
        args = get_args(btype)
        if isinstance(eq_origin, EnumTypeWrapper) or btype is ProtobufEnum:
            eq_origin = None
        if eq_origin is dict:
            tgttype = args[1]
        elif eq_origin is list:
            tgttype = args[0]
        else:
            tgttype = btype

        return (
            eq_origin,
            isinstance(tgttype, EnumTypeWrapper) or tgttype is ProtobufEnum,
        )

    return destruct_enum(modeltype) == destruct_enum(basetype)


def convert_timestamp(
    value: Timestamp,
    **kwargs: Any,
) -> datetime:

    ts = value.ToDatetime()
    start = kwargs.get("start")
    end = kwargs.get("end")

    if start is not None and ts < start:
        raise ValueError(f"Datetime value must be on or after {start}")
    if end is not None and ts > end:
        raise ValueError(f"Datetime value must be on or before {end}")

    return ts


def base_constrained_list(
    value: List[Any],
    **kwargs: Any,
) -> List[Any]:
    min_length = kwargs.get("min_length")
    max_length = kwargs.get("max_length")
    length = len(value)
    if min_length is not None and length < min_length:
        raise ValueError(
            f"List has {length} items, but should have at least {min_length}"  # ✅ FIXED
        )
    if max_length is not None and length > max_length:
        raise ValueError(
            f"List has {length} items, but should have at most {max_length}"  # ✅ FIXED
        )
    return value


def base_constrained_dict(
    value: Dict[Any, Any],
    **kwargs: Any,
) -> Dict[Any, Any]:
    constrained_list(list(value.values()), **kwargs)
    return value


protobuf_converts: Dict[Tuple[Hashable, Hashable], Callable[..., Any]] = {
    (Timestamp, datetime): convert_timestamp,
    (Struct, Struct): base_constrained_dict,
    (ListValue, ListValue): base_constrained_list,
}

arg_proc.update(protobuf_converts)

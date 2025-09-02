import importlib
from contextlib import suppress
from functools import lru_cache
from types import ModuleType

from google.protobuf.descriptor import FieldDescriptor
from google.protobuf.descriptor_pb2 import FieldDescriptorProto
from typemapping import get_args, get_origin
from typing_extensions import Any, Dict, List, Optional, Set, Type

from grpcAPI.datatypes import Message, ProtobufEnum

FD = FieldDescriptor
FDP = FieldDescriptorProto


def extract_message(ftype: Type[Any]) -> Optional[Type[Message]]:
    origin = get_origin(ftype)
    if origin is None:
        tgttype = ftype
    else:
        args = get_args(ftype)
        if origin is dict:
            tgttype = args[1]
        else:
            tgttype = args[0]
    if isinstance(tgttype, type) and issubclass(tgttype, Message):
        return tgttype
    return None


def inject_proto_typing(cls: Type[Any]) -> None:
    if not issubclass(cls, Message):
        raise RuntimeError  # pragma: no cover
    if getattr(cls, "__annotations__", None):
        return
    annotations = {}
    nested_msg: Set[Type[Message]] = set()
    for field in cls.DESCRIPTOR.fields:
        ftype = get_type(field, cls)
        annotations[field.name] = ftype
        basemessage = extract_message(ftype)
        if basemessage:
            nested_msg.add(basemessage)
    cls.__annotations__ = annotations

    for type_message in nested_msg:
        inject_proto_typing(type_message)


def get_type(field: FieldDescriptor, cls: Type[Any]) -> Type[Any]:
    if is_map_field(field):
        base_type = get_map_type(field, cls)
    elif is_list(field):
        base_type = get_list_type(field, cls)
    else:
        base_type = get_type_single(field, cls)

    if is_optional_field(field):
        return Optional[base_type]

    return base_type


def get_type_single(field: FieldDescriptor, cls: Type[Any]) -> Type[Any]:
    if field.type == FD.TYPE_MESSAGE:
        return get_message_type(field.message_type, cls)
    if field.type == FD.TYPE_ENUM:
        return ProtobufEnum
    return get_primary_type(field)


def is_optional_field(field: FieldDescriptor) -> bool:
    # Skip repeated fields - they're always List[T], never Optional[List[T]]
    if field.label == FieldDescriptor.LABEL_REPEATED:
        return False

    # Proto3 explicit optional ONLY (creates synthetic oneof with _fieldname)
    if (
        hasattr(field, "containing_oneof")
        and field.containing_oneof
        and field.containing_oneof.name.startswith("_")
    ):
        return True

    # Everything else is NOT optional:
    # - Regular messages: always have default instance (not None)
    # - Regular oneof: always have default value (not None)
    # - Primitives: always have default values (not None)

    return False


@lru_cache
def get_message_type(field: FieldDescriptor, cls: Type[Any]) -> Type[Any]:
    # Try to get the class directly from the descriptor's _concrete_class
    try:
        if hasattr(field, "_concrete_class") and field._concrete_class:
            return field._concrete_class
    except:
        pass

    # Alternative: try to get from the message_type descriptor
    try:
        if hasattr(field.message_type, "_concrete_class"):
            return field.message_type._concrete_class
    except:
        pass

    # Fallback to original logic with safer module resolution
    try:
        cls_module = get_module(cls)

        original_file = cls.DESCRIPTOR.file.name
        field_filename = field.file.name

        if field_filename == original_file:
            tgt_module = cls_module
        else:
            imported_str = get_protobuf_name(field_filename)
            tgt_module = getattr(cls_module, imported_str)

        # Recursive approach for nested types
        return resolve_nested_type(field.full_name, tgt_module, cls)
    except:
        # If all else fails, return Any as a safe fallback
        # from typing import Any
        # return Any
        raise ModuleNotFoundError(
            f"Could not resolve message type for field: {field.full_name}"
        )


def resolve_nested_type(
    full_name: str, module: ModuleType, root_cls: Type[Any]
) -> Type[Any]:
    """Recursively resolve nested message types"""
    parts = full_name.split(".")
    type_name = parts[-1]  # Always the last part is the actual type name

    # Try simple approach first (works for most cases)

    with suppress(AttributeError):
        return getattr(module, type_name)

    # If simple doesn't work, check if it's in the root class (same-file nested)
    if hasattr(root_cls, type_name):
        return getattr(root_cls, type_name)

    # Only try complex nested resolution if we have more than 2 parts
    # and it's not a well-known type
    if len(parts) > 2 and not (parts[0] == "google" and parts[1] == "protobuf"):
        message_path = parts[1:]  # Skip package name

        try:
            # Start with the outermost message
            current_type = getattr(module, message_path[0])

            # Navigate through nested messages
            for nested_name in message_path[1:]:
                current_type = getattr(current_type, nested_name)

            return current_type
        except AttributeError:
            pass

    # If all else fails
    raise AttributeError(f"Could not resolve type: {full_name} in module {module}")


def get_primary_type(field: FieldDescriptor) -> Type[Any]:
    ftype = field.type
    for k, v in _protobuf_to_python_map.items():
        if ftype in v:
            return k
    raise TypeError  # pragma: no cover


def get_map_type(field: FieldDescriptor, cls: Type[Any]) -> Type[Any]:
    key_field = field.message_type.fields_by_name["key"]
    value_field = field.message_type.fields_by_name["value"]

    key_type = get_type_single(key_field, cls)
    value_type = get_type_single(value_field, cls)

    return Dict[key_type, value_type]


def get_list_type(field: FieldDescriptor, cls: Type[Any]) -> Type[Any]:
    btype = get_type_single(field, cls)
    return List[btype]


def is_map_field(field: FieldDescriptor) -> bool:
    return (
        field.label == FD.LABEL_REPEATED
        and field.type == FD.TYPE_MESSAGE
        and field.message_type.GetOptions().map_entry
    )


def is_list(field: FieldDescriptor) -> bool:
    return field.label == FD.LABEL_REPEATED and (
        field.type != FD.TYPE_MESSAGE
        or (
            field.type == FD.TYPE_MESSAGE
            and not field.message_type.GetOptions().map_entry
        )
    )


_protobuf_to_python_map: Dict[Type[Any], List[FD]] = {
    float: [FD.TYPE_FLOAT, FD.TYPE_DOUBLE],
    int: [
        FD.TYPE_INT64,
        FD.TYPE_INT32,
        FD.TYPE_UINT64,
        FD.TYPE_UINT32,
        FD.TYPE_FIXED64,
        FD.TYPE_SINT32,
        FD.TYPE_SINT64,
        FD.TYPE_FIXED32,
        FD.TYPE_SFIXED32,
        FD.TYPE_SFIXED64,
    ],
    bool: [FD.TYPE_BOOL],
    bytes: [FD.TYPE_BYTES],
    str: [FD.TYPE_STRING],
}


def get_protobuf_name(name: str) -> str:
    return name.replace("/", "_dot_").replace(".proto", "__pb2")


def get_module(cls: Type[Any]) -> ModuleType:
    module_name = cls.__module__
    try:
        return importlib.import_module(module_name)
    except ModuleNotFoundError:
        # Simple fallback: add current directory to path and try again
        import os
        import sys

        if os.getcwd() not in sys.path:
            sys.path.insert(0, os.getcwd())

        return importlib.import_module(module_name)

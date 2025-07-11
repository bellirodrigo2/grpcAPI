import importlib
from types import ModuleType

from google.protobuf.descriptor import FieldDescriptor
from google.protobuf.descriptor_pb2 import FieldDescriptorProto
from typing_extensions import Any, Dict, List, Optional, Type

from grpcAPI.types import Message

FD = FieldDescriptor
FDP = FieldDescriptorProto


def inject_proto_typing(cls: Type[Any]) -> Optional[Dict[str, Type[Any]]]:
    if not issubclass(cls, Message):
        raise RuntimeError
    if cls.__annotations__:
        return None
    annotations = {}
    for field in cls.DESCRIPTOR.fields:
        type = get_type(field, cls)
        annotations[field.name] = type
    return annotations


def get_type(field: FieldDescriptor, cls: Type[Any]) -> Type[Any]:
    if is_map_field(field):
        return get_map_type(field, cls)
    if is_list(field):
        return get_list_type(field, cls)
    return get_type_single(field, cls)


def get_type_single(field: FieldDescriptor, cls: Type[Any]) -> Type[Any]:
    if field.type == FD.TYPE_MESSAGE:
        return get_message_type(field.message_type, cls)
    if field.type == FD.TYPE_ENUM:
        return get_message_type(field.enum_type, cls)
    return get_primary_type(field)


def get_message_type(field: FieldDescriptor, cls: Type[Any]) -> Type[Any]:

    cls_module = get_module(cls)

    original_file = cls.DESCRIPTOR.file.name
    field_filename = field.file.name
    if field_filename == original_file:
        tgt_module = cls_module
    else:
        imported_str = get_protobuf_name(field_filename)
        tgt_module = getattr(cls_module, imported_str)

    tgt_type = getattr(tgt_module, field.name)
    return tgt_type


def get_primary_type(field: FieldDescriptor) -> Type[Any]:
    ftype = field.type
    for k, v in _protobuf_to_python_map.items():
        if ftype in v:
            return k
    raise TypeError


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
    return (
        field.label == FD.LABEL_REPEATED
        and field.type == FD.TYPE_MESSAGE
        and not field.message_type.GetOptions().map_entry
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
    return importlib.import_module(module_name)

from typing import Dict

from google.protobuf.descriptor import FieldDescriptor
from google.protobuf.descriptor_pb2 import FieldDescriptorProto
from typing_extensions import Any, Type


def get_type(field: FieldDescriptor, cls: Type[Any]) -> Type[Any]:
    if is_map_field(field):
        return get_map_type(field, cls)
    if is_list(field):
        return get_list_type(field, cls)
    return get_type_single(field, cls)


def get_type_single(field: FieldDescriptor, cls: Type[Any]) -> Type[Any]:
    if FieldDescriptorProto.Type.Name(field.type) == FieldDescriptor.TYPE_MESSAGE:
        return get_message_type(field, cls)
    return get_base_type(field)


def get_message_type(field: FieldDescriptor, cls: Type[Any]) -> Type[Any]:
    # pegar key e value
    # usar get_single
    # retornar Dict[]
    # return Dict[cls,cls]
    pass


def get_base_type(field: FieldDescriptor) -> Type[Any]:
    pass


def get_map_type(field: FieldDescriptor, cls: Type[Any]) -> Type[Any]:
    pass


def get_list_type(field: FieldDescriptor, cls: Type[Any]) -> Type[Any]:
    pass


def is_map_field(field: FieldDescriptor) -> bool:
    return (
        field.label == FieldDescriptor.LABEL_REPEATED
        and field.type == FieldDescriptor.TYPE_MESSAGE
        and field.message_type.GetOptions().map_entry
    )


def is_list(field: FieldDescriptor) -> bool:
    return (
        field.label == FieldDescriptor.LABEL_REPEATED
        and field.type == FieldDescriptor.TYPE_MESSAGE
        and not field.message_type.GetOptions().map_entry
    )

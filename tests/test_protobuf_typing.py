from google.protobuf.descriptor import FieldDescriptor
from google.protobuf.descriptor_pb2 import FieldDescriptorProto

from tests.lib.user_pb2 import User


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


def test_() -> None:
    map_field = User.DESCRIPTOR.fields_by_name["dict"]

    key_type = map_field.message_type.fields_by_name["key"]
    value_type = map_field.message_type.fields_by_name["value"]
    print(FieldDescriptorProto.Type.Name(key_type.type))
    print(FieldDescriptorProto.Type.Name(value_type.type))

    repeated_field = User.DESCRIPTOR.fields_by_name["others"]
    print(repeated_field.label == FieldDescriptor.LABEL_REPEATED)  # True
    print(FieldDescriptorProto.Type.Name(repeated_field.type), repeated_field.name)

    for field in User.DESCRIPTOR.fields:
        print(field.name, is_list(field))

    # module_name = User.__module__

    # import importlib

    # module = importlib.import_module(module_name)
    # other = getattr(module, "other__pb2", None)
    # print(other.Other.__module__)
    # print(InnerMessage.__module__)
    # type_constants = {
    #     name: value
    #     for name, value in vars(FieldDescriptor).items()
    #     if name.startswith("TYPE_") and isinstance(value, int)
    # }

    # # print(type_constants)

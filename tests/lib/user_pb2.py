# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# NO CHECKED-IN PROTOBUF GENCODE
# source: user.proto
# Protobuf Python Version: 6.31.0
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder

_runtime_version.ValidateProtobufRuntimeVersion(
    _runtime_version.Domain.PUBLIC, 6, 31, 0, "", "user.proto"
)
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


import other_pb2 as other__pb2
from google.protobuf import timestamp_pb2 as google_dot_protobuf_dot_timestamp__pb2
from inner import inner_pb2 as inner_dot_inner__pb2
from multi.inner import class_pb2 as multi_dot_inner_dot_class__pb2

DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(
    b'\n\nuser.proto\x12\x08userpack\x1a\x11inner/inner.proto\x1a\x0bother.proto\x1a\x17multi/inner/class.proto\x1a\x1fgoogle/protobuf/timestamp.proto"\x8a\x05\n\x04User\x12 \n\x04\x63ode\x18\x01 \x01(\x0e\x32\x12.userpack.UserCode\x12 \n\x03\x61ge\x18\x02 \x01(\x0b\x32\x13.inner.InnerMessage\x12(\n\x04time\x18\x06 \x01(\x0b\x32\x1a.google.protobuf.Timestamp\x12\x14\n\x0c\x61\x66\x66illiation\x18\x03 \x01(\t\x12\x10\n\x04name\x18\x04 \x01(\tB\x02\x18\x01\x12\x15\n\x05other\x18\n \x01(\x0b\x32\x06.Other\x12\x12\n\x08\x65mployee\x18\x10 \x01(\tH\x00\x12\x10\n\x06school\x18\x11 \x01(\tH\x00\x12\x12\n\x08inactive\x18\x12 \x01(\x08H\x00\x12&\n\x04\x64ict\x18\x13 \x03(\x0b\x32\x18.userpack.User.DictEntry\x12\x16\n\x06others\x18\x14 \x03(\x0b\x32\x06.Other\x12\x16\n\x03msg\x18\x15 \x01(\x0b\x32\t.ClassMsg\x12+\n\x07map_msg\x18\x16 \x03(\x0b\x32\x1a.userpack.User.MapMsgEntry\x12!\n\x05\x63odes\x18\x17 \x03(\x0e\x32\x12.userpack.UserCode\x12/\n\tmap_codes\x18\x18 \x03(\x0b\x32\x1c.userpack.User.MapCodesEntry\x1a+\n\tDictEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\t:\x02\x38\x01\x1a\x42\n\x0bMapMsgEntry\x12\x0b\n\x03key\x18\x01 \x01(\x05\x12"\n\x05value\x18\x02 \x01(\x0b\x32\x13.inner.InnerMessage:\x02\x38\x01\x1a\x43\n\rMapCodesEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12!\n\x05value\x18\x02 \x01(\x0e\x32\x12.userpack.UserCode:\x02\x38\x01\x42\x0c\n\noccupation*;\n\x08UserCode\x12\x0c\n\x08\x45MPLOYEE\x10\x00\x12\x13\n\x06SCHOOL\x10\x89\xfe\xff\xff\xff\xff\xff\xff\xff\x01\x12\x0c\n\x08INACTIVE\x10\x01\x62\x06proto3'
)

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, "user_pb2", _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    DESCRIPTOR._loaded_options = None
    _globals["_USER_DICTENTRY"]._loaded_options = None
    _globals["_USER_DICTENTRY"]._serialized_options = b"8\001"
    _globals["_USER_MAPMSGENTRY"]._loaded_options = None
    _globals["_USER_MAPMSGENTRY"]._serialized_options = b"8\001"
    _globals["_USER_MAPCODESENTRY"]._loaded_options = None
    _globals["_USER_MAPCODESENTRY"]._serialized_options = b"8\001"
    _globals["_USER"].fields_by_name["name"]._loaded_options = None
    _globals["_USER"].fields_by_name["name"]._serialized_options = b"\030\001"
    _globals["_USERCODE"]._serialized_start = 767
    _globals["_USERCODE"]._serialized_end = 826
    _globals["_USER"]._serialized_start = 115
    _globals["_USER"]._serialized_end = 765
    _globals["_USER_DICTENTRY"]._serialized_start = 571
    _globals["_USER_DICTENTRY"]._serialized_end = 614
    _globals["_USER_MAPMSGENTRY"]._serialized_start = 616
    _globals["_USER_MAPMSGENTRY"]._serialized_end = 682
    _globals["_USER_MAPCODESENTRY"]._serialized_start = 684
    _globals["_USER_MAPCODESENTRY"]._serialized_end = 751
# @@protoc_insertion_point(module_scope)

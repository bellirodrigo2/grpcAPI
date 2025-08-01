"""
@generated by mypy-protobuf.  Do not edit manually!
isort:skip_file
"""

import builtins
import google.protobuf.descriptor
import google.protobuf.message
import google.protobuf.struct_pb2
import google.protobuf.timestamp_pb2
import typing

DESCRIPTOR: google.protobuf.descriptor.FileDescriptor

@typing.final
class AccountInput(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    NAME_FIELD_NUMBER: builtins.int
    EMAIL_FIELD_NUMBER: builtins.int
    PAYLOAD_FIELD_NUMBER: builtins.int
    ITENS_FIELD_NUMBER: builtins.int
    name: builtins.str
    email: builtins.str
    @property
    def payload(self) -> google.protobuf.struct_pb2.Struct: ...
    @property
    def itens(self) -> google.protobuf.struct_pb2.ListValue: ...
    def __init__(
        self,
        *,
        name: builtins.str = ...,
        email: builtins.str = ...,
        payload: google.protobuf.struct_pb2.Struct | None = ...,
        itens: google.protobuf.struct_pb2.ListValue | None = ...,
    ) -> None: ...
    def HasField(
        self, field_name: typing.Literal["itens", b"itens", "payload", b"payload"]
    ) -> builtins.bool: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "email", b"email", "itens", b"itens", "name", b"name", "payload", b"payload"
        ],
    ) -> None: ...

global___AccountInput = AccountInput

@typing.final
class AccountCreated(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    ID_FIELD_NUMBER: builtins.int
    CREATED_AT_FIELD_NUMBER: builtins.int
    id: builtins.str
    @property
    def created_at(self) -> google.protobuf.timestamp_pb2.Timestamp: ...
    def __init__(
        self,
        *,
        id: builtins.str = ...,
        created_at: google.protobuf.timestamp_pb2.Timestamp | None = ...,
    ) -> None: ...
    def HasField(
        self, field_name: typing.Literal["created_at", b"created_at"]
    ) -> builtins.bool: ...
    def ClearField(
        self, field_name: typing.Literal["created_at", b"created_at", "id", b"id"]
    ) -> None: ...

global___AccountCreated = AccountCreated

@typing.final
class Account(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    NAME_FIELD_NUMBER: builtins.int
    EMAIL_FIELD_NUMBER: builtins.int
    PAYLOAD_FIELD_NUMBER: builtins.int
    ITENS_FIELD_NUMBER: builtins.int
    ID_FIELD_NUMBER: builtins.int
    CREATED_AT_FIELD_NUMBER: builtins.int
    name: builtins.str
    email: builtins.str
    id: builtins.str
    @property
    def payload(self) -> google.protobuf.struct_pb2.Struct: ...
    @property
    def itens(self) -> google.protobuf.struct_pb2.ListValue: ...
    @property
    def created_at(self) -> google.protobuf.timestamp_pb2.Timestamp: ...
    def __init__(
        self,
        *,
        name: builtins.str = ...,
        email: builtins.str = ...,
        payload: google.protobuf.struct_pb2.Struct | None = ...,
        itens: google.protobuf.struct_pb2.ListValue | None = ...,
        id: builtins.str = ...,
        created_at: google.protobuf.timestamp_pb2.Timestamp | None = ...,
    ) -> None: ...
    def HasField(
        self,
        field_name: typing.Literal[
            "created_at", b"created_at", "itens", b"itens", "payload", b"payload"
        ],
    ) -> builtins.bool: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "created_at",
            b"created_at",
            "email",
            b"email",
            "id",
            b"id",
            "itens",
            b"itens",
            "name",
            b"name",
            "payload",
            b"payload",
        ],
    ) -> None: ...

global___Account = Account

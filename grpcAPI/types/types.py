from typing import Any, List, Type

from grpcAPI.types.base import BaseProto


class BaseField(BaseProto):
    @classmethod
    def qualified_prototype(cls) -> str:
        return cls.prototype()


class BaseStringField(str, BaseField):
    pass


class BaseIntField(int, BaseField):
    pass


class BaseFloatField(float, BaseField):
    pass


class BaseBytesField(bytes, BaseField):
    pass


class BaseBoolField(BaseField):
    def __init__(self, value: bool = False) -> None:
        self._value = bool(value)

    def __bool__(self) -> bool:
        return self._value

    def __repr__(self) -> str:
        return str(self._value)


class Double(BaseFloatField):
    @classmethod
    def prototype(cls) -> str:
        return "double"


class Float(BaseFloatField):
    @classmethod
    def prototype(cls) -> str:
        return "float"


class Int32(BaseIntField):
    @classmethod
    def prototype(cls) -> str:
        return "int32"


class Int64(BaseIntField):
    @classmethod
    def prototype(cls) -> str:
        return "int64"


class UInt32(BaseIntField):
    @classmethod
    def prototype(cls) -> str:
        return "uint32"


class UInt64(BaseIntField):
    @classmethod
    def prototype(cls) -> str:
        return "uint64"


class SInt32(BaseIntField):
    @classmethod
    def prototype(cls) -> str:
        return "sint32"


class SInt64(BaseIntField):
    @classmethod
    def prototype(cls) -> str:
        return "sint64"


class Fixed32(BaseIntField):
    @classmethod
    def prototype(cls) -> str:
        return "fixed32"


class Fixed64(BaseIntField):
    @classmethod
    def prototype(cls) -> str:
        return "fixed64"


class SFixed32(BaseIntField):
    @classmethod
    def prototype(cls) -> str:
        return "sfixed32"


class SFixed64(BaseIntField):
    @classmethod
    def prototype(cls) -> str:
        return "sfixed64"


class Bool(BaseBoolField):
    @classmethod
    def prototype(cls) -> str:
        return "bool"


class String(BaseStringField):
    @classmethod
    def prototype(cls) -> str:
        return "string"


class Bytes(BaseBytesField):
    @classmethod
    def prototype(cls) -> str:
        return "bytes"


DEFAULT_PRIMITIVES: dict[type[Any], Type[BaseField]] = {
    str: String,
    int: Int64,
    float: Float,
    bytes: Bytes,
    bool: Bool,
}

allowed_map_key: List[type[Any]] = [
    int,
    str,
    bool,
    Int32,
    Int64,
    UInt32,
    UInt64,
    SInt32,
    SInt64,
    Fixed32,
    Fixed64,
    SFixed32,
    SFixed64,
    Bool,
    String,
]

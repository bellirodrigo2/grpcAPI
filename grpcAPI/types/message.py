from enum import IntEnum
from typing import Any, List, Optional, Tuple, Union

from grpcAPI.types.base import BaseProto, ProtoOption
from grpcAPI.types.method import if_stream_get_type


class _NoPackage:
    def __repr__(self) -> str:
        return "NO_PACkAGE"

    def __str__(self) -> str:
        return "NO_PACKAGE"


NO_PACKAGE = _NoPackage()


class Module:
    @classmethod
    def protofile(cls) -> str:
        raise NotImplementedError(
            f"protofile() must be implemented by the subclass. Not Found for: {cls.__name__}"
        )

    @classmethod
    def package(cls) -> Union[str, object]:
        return NO_PACKAGE


class Meta:

    @classmethod
    def description(cls) -> str:
        return ""

    @classmethod
    def options(cls) -> ProtoOption:
        return ProtoOption()

    @classmethod
    def reserved(cls) -> List[Union[int, range, str]]:
        return []


class SelfNamePrototype(BaseProto, Module):
    @classmethod
    def prototype(cls) -> str:
        return cls.__name__

    @classmethod
    def qualified_prototype(cls) -> str:
        pack = cls.package()
        if isinstance(pack, _NoPackage):
            return cls.prototype()
        return f"{str(pack)}.{cls.prototype()}"


class BaseMessage(SelfNamePrototype, Meta):
    pass


class BaseEnum(SelfNamePrototype, Meta, IntEnum):
    pass


def is_BaseMessage(tgt: type[Any]) -> bool:
    return get_BaseMessage(tgt) is not None


def get_BaseMessage(tgt: type[Any]) -> Optional[type[Any]]:
    basetype = if_stream_get_type(tgt)
    bt = basetype or tgt
    if not isinstance(bt, type):
        return None
    if issubclass(bt, BaseMessage) or issubclass(bt, BaseEnum):
        return bt
    return None


# ---------------- Extract Class Info ---------------------------------------


def get_module(cls: type[BaseMessage]) -> Tuple[str, Union[str, _NoPackage]]:
    protofile_attr = getattr(cls, "protofile", None)
    if not callable(protofile_attr):
        raise TypeError(
            f"{cls.__name__} must define a callable 'protofile' classmethod."
        )
    protofile = protofile_attr()

    package_attr = getattr(cls, "package", None)
    package = package_attr() if callable(package_attr) else NO_PACKAGE

    return protofile, package


def get_description_options(
    cls: type[BaseMessage],
) -> Tuple[str, ProtoOption]:
    description_method = getattr(cls, "description", None)
    description: str = description_method() if callable(description_method) else ""

    options_method = getattr(cls, "options", None)
    options: ProtoOption = (
        options_method() if callable(options_method) else ProtoOption()
    )

    return description, options


def get_headers(
    cls: type[BaseMessage],
) -> Tuple[str, Union[str, _NoPackage], str, ProtoOption, List[Union[int, range, str]]]:

    protofile, package = get_module(cls)
    description, options = get_description_options(cls)

    reserved_attr = getattr(cls, "reserved", None)
    reserved: List[Union[int, range, str]] = (
        reserved_attr() if callable(reserved_attr) else []
    )
    return protofile, package, description, options, reserved

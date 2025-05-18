from typing import List, Optional, Tuple, Union

from grpcAPI.types.base import BaseProto, ProtoOption

NO_PACKAGE = object()


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


class BaseMessage(BaseProto, Module, Meta):

    @classmethod
    def prototype(cls) -> str:
        return cls.__name__

    @classmethod
    def qualified_prototype(cls) -> str:
        return f"{cls.package()}.{cls.__name__}"


# ---------------- Extract Class Info ---------------------------------------


def get_module(
    cls: type[BaseMessage],
) -> Tuple[Optional[str], Optional[str]]:
    protofile_method = getattr(cls, "protofile", None)
    protofile: Optional[str] = None if protofile_method is None else protofile_method()

    package_method = getattr(cls, "package", None)
    package: Optional[str] = None if package_method is None else package_method()

    return protofile, package


def get_description_options(
    cls: type[BaseMessage],
) -> Tuple[str, ProtoOption]:
    description_method = getattr(cls, "description", None)
    description: str = "" if description_method is None else description_method()

    options_method = getattr(cls, "options", None)
    options: ProtoOption = ProtoOption() if options_method is None else options_method()

    return description, options


def extract_reserveds(
    reserveds: List[Union[int, range, str]],
) -> Tuple[List[Union[int, range]], List[str]]:

    keys: List[str] = [item for item in reserveds if isinstance(item, str)]
    indexes: List[Union[int, range]] = [
        item for item in reserveds if not isinstance(item, str)
    ]

    return indexes, keys


def get_headers(
    cls: type[BaseMessage],
) -> Tuple[
    Optional[str], Optional[str], str, ProtoOption, List[Union[int, range]], List[str]
]:

    protofile, package = get_module(cls)
    description, options = get_description_options(cls)

    reserved_method = getattr(cls, "reserved_index", None)
    reserved: List[Union[int, range, str]] = (
        [] if reserved_method is None else reserved_method()
    )
    reserved_indexes, reserved_keys = extract_reserveds(reserved)
    return protofile, package, description, options, reserved_indexes, reserved_keys

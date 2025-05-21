from dataclasses import dataclass, field
from enum import Enum, IntEnum
from typing import Any, Callable, Dict, List, Union

from grpcAPI.proto_proxy import ProtoProxy
from grpcAPI.types.base import ProtoOption
from grpcAPI.types.message import NO_PACKAGE, BaseMessage


def create_proto_model(
    base_cls: type[Any], protofile: str, package: Union[str, object]
) -> type:
    class GeneratedProto(base_cls):
        @classmethod
        def protofile(cls) -> str:
            return protofile

        @classmethod
        def package(cls) -> Union[str, object]:
            return package

    GeneratedProto.__name__ = f"{base_cls.__name__}Proto"
    return GeneratedProto


class ProtoModel(BaseMessage, ProtoProxy):
    pass


@dataclass
class MethodPack:
    description: str
    options: ProtoOption
    method: Callable[..., Any]


@dataclass(frozen=True)
class Module:
    modname: str
    package: Union[object, str] = field(default=NO_PACKAGE)
    _services: Dict[str, MethodPack] = field(default_factory=dict[str, MethodPack])
    _model: type[BaseMessage] = ProtoModel

    def __post_init__(self) -> None:
        proto_cls = create_proto_model(self._model, self.modname, self.package)
        object.__setattr__(self, "_proto_model", proto_cls)
        proto_enum = create_proto_model(IntEnum, self.modname, self.package)
        object.__setattr__(self, "_proto_enum", proto_enum)

    @property
    def ProtoModel(self) -> type[BaseMessage]:
        return self._proto_model

    @property
    def ProtoEnum(self) -> type[Enum]:
        return self._proto_enum

    def add_service(
        self,
        servicename: str,
        method: Callable[..., Any],
        description: str,
        options: ProtoOption,
    ) -> None:
        self._services[servicename] = MethodPack(
            description,
            options,
            method,
        )

    def service(
        self,
        servicename: str,
        description: str,
        options: ProtoOption,
    ) -> Callable[..., Any]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            self.add_service(servicename, func, description, options)
            return func

        return decorator


@dataclass(frozen=True)
class Package:

    packname: str
    modules: Dict[str, Module] = field(default_factory=dict[str, Module])

    def make_module(self, modname: str) -> Module:
        if modname in self.modules:
            raise ValueError
        module = Module(modname=modname, package=self.packname)
        self.modules[modname] = module
        return module

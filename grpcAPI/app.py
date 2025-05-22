from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum, IntEnum
from typing import Any, Callable, Dict, List, Union

from grpcAPI.proto_proxy import ProtoProxy
from grpcAPI.types import NO_PACKAGE, BaseMessage, ProtoOption, _NoPackage


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
    packname: Union[_NoPackage, str] = field(default=NO_PACKAGE)
    _services: Dict[str, List[MethodPack]] = field(
        default_factory=lambda: defaultdict(list)
    )
    _model: type[BaseMessage] = ProtoModel

    def __post_init__(self) -> None:
        proto_cls = create_proto_model(self._model, self.modname, self.packname)
        object.__setattr__(self, "_proto_model", proto_cls)
        proto_enum = create_proto_model(IntEnum, self.modname, self.packname)
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
        methodpack = MethodPack(description, options, method)
        self._services[servicename].append(methodpack)

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
        module = Module(modname=modname, packname=self.packname)
        self.add_module(module)
        return module

    def add_module(self, module: Module) -> None:
        modname = module.modname
        modules = self.modules
        if modname in modules:
            raise ValueError(
                f"Module '{modname}' already exists in package '{self.packname}'."
            )
        modules[modname] = module


@dataclass(frozen=True)
class App:

    packages: Dict[Union[_NoPackage, str], Package] = field(
        default_factory=dict[Union[_NoPackage, str], Package]
    )

    def add_package(self, package: Package) -> None:
        thispackages = self.packages
        packname = package.packname
        if packname in thispackages:
            raise ValueError
        thispackages[packname] = package

    def add_module(self, module: Module) -> None:
        package = self.packages.get(module.packname)
        if package is None:
            raise ValueError(f"Package '{module.packname}' not found in App.")
        package.add_module(module)


if __name__ == "__main__":

    app = App()

    pack1 = Package("pack1")
    mod1 = pack1.make_module("modservice1")

    class MyRequest(mod1.ProtoModel):
        user: str

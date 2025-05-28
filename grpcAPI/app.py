from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, Iterator, List, Optional, Set, Union

from grpcAPI.proto_proxy import ProtoProxy
from grpcAPI.typemapping import map_service_classes
from grpcAPI.types import NO_PACKAGE, BaseMessage, ProtoOption, _NoPackage
from grpcAPI.types.interfaces import IMethod, IModule, IPackage, IService
from grpcAPI.types.message import BaseEnum


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
class MethodPack(IMethod):
    method: Callable[..., Any]
    description: str
    options: ProtoOption


@dataclass
class ServicePack(IService):
    name: str
    module: str
    package: Union[str, _NoPackage]
    methods: List[IMethod]
    description: str
    options: ProtoOption


@dataclass(frozen=True)
class Module(IModule):
    name: str
    package: Union[_NoPackage, str] = field(default=NO_PACKAGE)

    description: str = field(default="")
    options: ProtoOption = field(default_factory=ProtoOption)
    _services: List[IService] = field(default_factory=list[IService])
    _model: type[BaseMessage] = ProtoModel

    def __post_init__(self) -> None:
        proto_cls = create_proto_model(self._model, self.name, self.package)
        object.__setattr__(self, "_proto_model", proto_cls)
        proto_enum = create_proto_model(BaseEnum, self.name, self.package)
        object.__setattr__(self, "_proto_enum", proto_enum)

    @property
    def services(self) -> List[IService]:
        return self._services

    @property
    def objects(self) -> Set[type[Union[BaseMessage, BaseEnum]]]:
        all_methods: List[Callable[..., Any]] = [
            method_pack.method
            for service_pack in self._services
            for method_pack in service_pack.methods
        ]
        return map_service_classes(all_methods)

    @property
    def ProtoModel(self) -> type[BaseMessage]:
        return self._proto_model  # type: ignore

    @property
    def ProtoEnum(self) -> type[Enum]:
        return self._proto_enum  # type: ignore

    # def __iter__(self) -> Iterator[IService]:
    # return iter(self._services)

    def Service(
        self,
        servicename: str,
        description: str = "",
        options: Optional[ProtoOption] = None,
    ) -> Callable[..., Callable[[Callable[..., Any]], Callable[..., Any]]]:

        servicepack = ServicePack(
            name=servicename,
            module=self.name,
            package=self.package,
            methods=[],
            description=description,
            options=options or ProtoOption(),
        )
        self._services.append(servicepack)

        def with_meta(
            description: str = "", options: Optional[ProtoOption] = None
        ) -> Callable[..., Callable[..., Any]]:
            options = options or ProtoOption()

            def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
                methodpack = MethodPack(
                    method=func, description=description, options=options
                )
                servicepack.methods.append(methodpack)
                return func

            return decorator

        return with_meta


@dataclass(frozen=True)
class Package(IPackage):

    name: Union[_NoPackage, str]
    _modules: Dict[str, IModule] = field(default_factory=dict[str, IModule])

    @property
    def modules(self) -> List[IModule]:
        return list(self._modules.values())

    def Module(
        self,
        modname: str,
        description: str = "",
        options: Optional[Dict[str, Any]] = None,
    ) -> Module:
        module = Module(
            name=modname,
            package=self.name,
            description=description,
            options=options or ProtoOption(),
        )
        self._add_module(module)
        return module

    def _add_module(self, module: IModule) -> None:
        modname = module.name
        modules = self._modules
        if modname in modules:
            raise ValueError(
                f"Module '{modname}' already exists in package '{self.name}'."
            )
        modules[modname] = module


@dataclass(frozen=True)
class App:

    name: str
    _packages: Dict[Union[_NoPackage, str], IPackage] = field(
        default_factory=dict[Union[_NoPackage, str], IPackage]
    )

    @property
    def packages(self) -> List[IPackage]:
        return list(self._packages.values())

    def add_package(self, package: Package) -> None:
        thispackages = self._packages
        packname = package.name
        if packname in thispackages:
            raise ValueError(f"Package '{packname}' already exists.")
        thispackages[packname] = package

    def add_module(self, module: Module) -> None:
        package = self._packages.get(module.package)
        if package is None:
            newpack = Package(module.package)
            self.add_package(newpack)
            package = newpack
        package._add_module(module)


if __name__ == "__main__":

    app = App()

    pack1 = Package("pack1")

    mod1 = Module("objmodule")

    class MyRequest(mod1.ProtoModel):
        user: str

    class MyResponse(mod1.ProtoModel):
        id: int

    mod2 = Module("servmodule")
    serv2 = mod2.Service("serv1")

    @serv2(description="Method comment here", options={"foo": "bar"})
    def method1(req: MyRequest) -> MyResponse:
        return MyResponse()

    app.add_module(mod2)

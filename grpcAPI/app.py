from dataclasses import dataclass, field
from enum import Enum, IntEnum
from typing import Any, Callable, Dict, Iterator, List, Optional, Union

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
    method: Callable[..., Any]
    description: str
    options: ProtoOption


@dataclass
class ServicePack:
    servname: str
    modname: str
    packname: Union[str, _NoPackage]
    methods: List[MethodPack]
    description: str
    options: ProtoOption


@dataclass(frozen=True)
class Module:
    modname: str
    packname: Union[_NoPackage, str] = field(default=NO_PACKAGE)

    description: str = field(default="")
    options: ProtoOption = field(default_factory=ProtoOption)
    _services: List[ServicePack] = field(default_factory=list[ServicePack])
    _model: type[BaseMessage] = ProtoModel

    def __post_init__(self) -> None:
        proto_cls = create_proto_model(self._model, self.modname, self.packname)
        object.__setattr__(self, "_proto_model", proto_cls)
        proto_enum = create_proto_model(IntEnum, self.modname, self.packname)
        object.__setattr__(self, "_proto_enum", proto_enum)

    @property
    def ProtoModel(self) -> type[BaseMessage]:
        return self._proto_model  # type: ignore

    @property
    def ProtoEnum(self) -> type[Enum]:
        return self._proto_enum  # type: ignore

    def __iter__(self) -> Iterator[ServicePack]:
        return iter(self._services)

    def Service(
        self,
        servicename: str,
        description: str = "",
        options: Optional[ProtoOption] = None,
    ) -> Callable[..., Callable[[Callable[..., Any]], Callable[..., Any]]]:

        servicepack = ServicePack(
            servname=servicename,
            modname=self.modname,
            packname=self.packname,
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
class Package:

    packname: str
    _modules: Dict[str, Module] = field(default_factory=dict[str, Module])

    def __iter__(self) -> Iterator[Module]:
        return iter(self._modules.values())

    def Module(self, modname: str) -> Module:
        module = Module(modname=modname, packname=self.packname)
        self._add_module(module)
        return module

    def _add_module(self, module: Module) -> None:
        modname = module.modname
        modules = self._modules
        if modname in modules:
            raise ValueError(
                f"Module '{modname}' already exists in package '{self.packname}'."
            )
        modules[modname] = module


@dataclass(frozen=True)
class App:

    _packages: Dict[Union[_NoPackage, str], Package] = field(
        default_factory=dict[Union[_NoPackage, str], Package]
    )

    def add_package(self, package: Package) -> None:
        thispackages = self._packages
        packname = package.packname
        if packname in thispackages:
            raise ValueError(f"Package '{packname}' already exists.")
        thispackages[packname] = package

    def add_module(self, module: Module) -> None:
        package = self._packages.get(module.packname)
        if package is None:
            raise ValueError(f"Package '{module.packname}' not found in App.")
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

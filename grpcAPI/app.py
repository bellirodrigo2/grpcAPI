import re
from dataclasses import dataclass, field
from enum import Enum
from typing import (
    Any,
    AsyncGenerator,
    Callable,
    Dict,
    List,
    Optional,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
)

from grpcAPI.ctxinject.validate import arg_proc
from grpcAPI.exceptionhandler import ErrorCode, ExceptionRegistry
from grpcAPI.mapclss import map_service_classes
from grpcAPI.proto_proxy import ProtoProxy
from grpcAPI.singleton import SingletonMeta
from grpcAPI.types import (
    NO_PACKAGE,
    BaseEnum,
    BaseMessage,
    IMethod,
    IModule,
    IPackage,
    IService,
    ProtoOption,
    _NoPackage,
)


def create_proto_model(
    base_cls: Type[Any], protofile: str, package: Union[str, object]
) -> Type[Any]:
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


def set_label(
    func: Callable[..., Any], package: str, module: str, service: str
) -> None:
    func.__grpcAPI_label__ = (package, module, service)


def get_label(func: Callable[..., Any]) -> Tuple[str, str, str]:
    label = getattr(func, "__grpcAPI_label__", None)
    return label


@dataclass(frozen=True)
class Module(IModule):
    name: str
    package: Union[_NoPackage, str] = field(default=NO_PACKAGE)

    description: str = field(default="")
    options: ProtoOption = field(default_factory=ProtoOption)
    _services: List[IService] = field(default_factory=list[IService])
    _model: Type[BaseMessage] = ProtoModel

    def __post_init__(self) -> None:
        proto_cls = create_proto_model(self._model, self.name, self.package)
        object.__setattr__(self, "_proto_model", proto_cls)
        proto_enum = create_proto_model(BaseEnum, self.name, self.package)
        object.__setattr__(self, "_proto_enum", proto_enum)

    @property
    def services(self) -> List[IService]:
        return self._services

    @property
    def objects(self) -> Set[Type[Union[BaseMessage, BaseEnum]]]:
        all_methods: List[Callable[..., Any]] = [
            method_pack.method
            for service_pack in self._services
            for method_pack in service_pack.methods
        ]
        return map_service_classes(all_methods)

    @property
    def ProtoModel(self) -> Type[BaseMessage]:
        return self._proto_model  # type: ignore

    @property
    def ProtoEnum(self) -> Type[Enum]:
        return self._proto_enum  # type: ignore

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
                set_label(func, self.package, self.name, servicename)
                return func

            return decorator

        return with_meta


VALID_PACKAGE_RE = re.compile(r"^([a-zA-Z_][a-zA-Z0-9_]*)(\.[a-zA-Z_][a-zA-Z0-9_]*)*$")


@dataclass(frozen=True)
class Package(IPackage):

    def __post_init__(self) -> None:
        if self.name != NO_PACKAGE and not bool(VALID_PACKAGE_RE.match(self.name)):
            raise ValueError(
                f'Package name "{self.name}" is not valid. Only, letters, numbers, underscore and dot is allowed'
            )

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
class App(metaclass=SingletonMeta):

    name: Optional[str] = None
    version: Optional[int] = None
    lifespan: Optional[Callable[[Any], AsyncGenerator[None, None]]] = None
    dependency_overrides: Dict[Callable[..., Any], Callable[..., Any]] = field(
        default_factory=dict[Callable[..., Any], Callable[..., Any]]
    )
    error_log: Optional[Callable[[str, Exception], None]] = None
    _packages: Dict[Union[_NoPackage, str], IPackage] = field(
        default_factory=dict[Union[_NoPackage, str], IPackage]
    )
    _exception_handlers: ExceptionRegistry = field(default_factory=dict)
    _caster: Dict[Tuple[type[Any], Type[Any]], Callable[..., Any]] = field(
        default_factory=lambda: dict(arg_proc)
    )
    _add_casting: Optional[Callable[["App"], None]] = None

    @property
    def casting_dict(self) -> Dict[Tuple[type[Any], Type[Any]], Callable[..., Any]]:
        if self._add_casting is not None:
            self._add_casting(self)
        return self._caster

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

    def add_exception_handler(
        self,
        exc_type: Type[Exception],
        handler: Callable[[Exception], Tuple[ErrorCode, str]],
    ) -> None:
        self._exception_handlers[exc_type] = handler

    def exception_handler(self, exc_type: Type[Exception]) -> Callable[
        [Callable[[Exception], Tuple[ErrorCode, str]]],
        Callable[[Exception], Tuple[ErrorCode, str]],
    ]:
        def decorator(
            func: Callable[[Exception], Tuple[ErrorCode, str]],
        ) -> Callable[[Exception], Tuple[ErrorCode, str]]:
            self.add_exception_handler(exc_type, func)
            return func

        return decorator


def get_models(
    func: Callable[..., Any], from_type: Any, to_subclass: Any
) -> List[Type[Any]]:
    models: List[Type[Any]] = []

    return models


T = TypeVar("T")
U = TypeVar("U")


def add_models(app: App, from_type: T, to_subclass: U, cast: Callable[[T], U]) -> None:

    funcs: List[Callable[..., Any]] = []
    for package in app.packages:
        for module in package.modules:
            for service in module.services:
                for method in service.methods:
                    funcs.append(method.method)

    for func in funcs:
        models = get_models(func, from_type, to_subclass)
        for model in models:
            key = (from_type, model)
            if key in app._caster.keys():
                continue
            app._caster[key] = cast

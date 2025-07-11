from types import ModuleType
from typing import Tuple

from makeproto import IService
from typing_extensions import Any, Callable, Dict, Type

from grpcAPI.exceptionhandler import ExceptionRegistry
from grpcAPI.interface import IServiceModule, MakeMethod


def provide_service(
    service: IService,
    module: IServiceModule,
    make_method: MakeMethod,
    overrides: Dict[Callable[..., Any], Callable[..., Any]],
    exception_registry: ExceptionRegistry,
) -> Type[Any]:

    methods: Dict[str, Callable[..., Any]] = {}
    for labeledmethod in service.methods:
        method = make_method(labeledmethod, overrides, exception_registry)
        methods[labeledmethod.name] = method

    methods["_get_module_"] = lambda _: module
    baseclass = module.get_service_baseclass(service.name)
    return type(service.name, (baseclass,), methods)


class classproperty:
    def __init__(self, fget) -> None:
        self.fget = classmethod(fget)

    def __get__(self, obj, owner) -> Any:
        return self.fget.__get__(obj, owner)()

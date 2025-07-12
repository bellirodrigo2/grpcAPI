from functools import partial
from typing import Generator, List

from makeproto import IService
from typing_extensions import Any, Callable, Dict, Type

from grpcAPI.config import MAKE_METHOD_ASYNC
from grpcAPI.exceptionhandler import ExceptionRegistry
from grpcAPI.interface import IServiceModule, MakeMethod


def provide_services_(
    services: List[IService],
    modules: Dict[str, Dict[str, IServiceModule]],
    make_method: MakeMethod,
    overrides: Dict[Callable[..., Any], Callable[..., Any]],
    exception_registry: ExceptionRegistry,
) -> Generator[Type[Any], Any, None]:
    for service in services:
        module_package = modules.get(service.package, {})
        for service_module in module_package.values():
            yield provide_service(
                service=service,
                module=service_module,
                make_method=make_method,
                overrides=overrides,
                exception_registry=exception_registry,
            )


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


provide_services = partial(provide_services_, make_method=MAKE_METHOD_ASYNC)

from collections.abc import AsyncIterator

from ctxinject.inject import get_mapped_ctx, resolve_mapped_ctx
from makeproto import ILabeledMethod, IService
from typing_extensions import Any, Callable, Dict, Generator, List, Type

from grpcAPI.context import AsyncContext
from grpcAPI.exceptionhandler import ExceptionRegistry
from grpcAPI.interfaces import ServiceModule


def provide_services(
    services: List[IService],
    modules: Dict[str, Dict[str, ServiceModule]],
    overrides: Dict[Callable[..., Any], Callable[..., Any]],
    exception_registry: ExceptionRegistry,
) -> Generator[Type[Any], Any, None]:
    for service in services:
        module_package = modules.get(service.package, {})
        for service_module in module_package.values():
            yield provide_service(
                service=service,
                module=service_module,
                overrides=overrides,
                exception_registry=exception_registry,
            )


def provide_service(
    service: IService,
    module: ServiceModule,
    overrides: Dict[Callable[..., Any], Callable[..., Any]],
    exception_registry: ExceptionRegistry,
) -> Type[Any]:

    methods: Dict[str, Callable[..., Any]] = {}
    for labeledmethod in service.methods:
        method = make_method_async(labeledmethod, overrides, exception_registry)
        methods[labeledmethod.name] = method

    methods["_get_module"] = lambda _: module
    methods["_get_label"] = lambda _: (service.package, service.name)
    baseclass = module.get_service_baseclass(service.name)
    return type(service.name, (baseclass,), methods)


def make_method_async(
    labeledmethod: ILabeledMethod,
    overrides: Dict[Callable[..., Any], Callable[..., Any]],
    exception_registry: ExceptionRegistry,
) -> Callable[..., Any]:
    """Async implementarion for MakeMethod using ctxinject"""

    try:
        req_t = labeledmethod.request_types[0]
        func = labeledmethod.method
        is_stream = labeledmethod.response_types.origin is AsyncIterator
    except (AttributeError, IndexError) as e:
        raise RuntimeError from e
    mapped_ctx = get_mapped_ctx(
        func=func,
        context={req_t.argtype: None, AsyncContext: None},
        allow_incomplete=False,
        validate=True,
        overrides=overrides,
    )

    async def method(self: Any, request: Any, context: AsyncContext) -> Any:
        try:
            ctx = {req_t.argtype: request, AsyncContext: context}
            kwargs = await resolve_mapped_ctx(ctx, mapped_ctx)
            response = await func(**kwargs)
            return response
        except Exception as e:
            exc_handler = exception_registry.get(type(e), None)
            if exc_handler is not None:
                err_code, err_msg = exc_handler(e)
                context.set_trailing_metadata(
                    (
                        ("error-type", e.__class__.__name__),
                        # ("custom-detail", "additional info here"),
                    )
                )
                await context.abort(err_code.value, err_msg)
            else:
                raise e

    async def stream_method(self: Any, request: Any, context: AsyncContext) -> Any:
        try:
            ctx = {req_t.argtype: request, AsyncContext: context}
            kwargs = await resolve_mapped_ctx(ctx, mapped_ctx)
            async for resp in func(**kwargs):
                yield resp
        except Exception as e:
            exc_handler = exception_registry.get(type(e), None)
            if exc_handler is not None:
                err_code, err_msg = exc_handler(e)
                context.set_trailing_metadata(
                    (
                        ("error-type", e.__class__.__name__),
                        # ("custom-detail", "additional info here"),
                    )
                )
                await context.abort(err_code.value, err_msg)
            else:
                raise e

    return stream_method if is_stream else method

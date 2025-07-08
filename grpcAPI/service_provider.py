from collections.abc import AsyncIterator

from ctxinject.inject import get_mapped_ctx, resolve_mapped_ctx
from makeproto import IService
from typing_extensions import Any, Callable, Dict, Optional, Tuple, Type

from grpcAPI.exceptionhandler import ExceptionRegistry
from grpcAPI.interface import IServiceModule
from grpcAPI.types import AsyncContext


def provide_services_async(
    service: IService,
    module: IServiceModule,
    overrides: Dict[Callable[..., Any], Callable[..., Any]],
    exception_registry: ExceptionRegistry,
    error_log: Optional[Callable[[str, Exception], None]] = None,
) -> Type[Any]:

    methods: Dict[str, Callable[..., Any]] = {}
    for labeledmethod in service.methods:
        try:
            req_t = labeledmethod.request_types[0]
            func = labeledmethod.method
            is_stream = labeledmethod.response_types.origin is AsyncIterator
        except (AttributeError, IndexError) as e:
            raise RuntimeError from e

        method = make_method(
            func=func,
            req_t=req_t,
            is_stream=is_stream,
            overrides=overrides,
            exception_registry=exception_registry,
            error_log=error_log,
        )
        methods[labeledmethod.name] = method
    service_class = make_service_class(service, module, methods)
    return service_class


def make_method(
    func: Callable[..., Any],
    req_t: Type[Any],
    is_stream: bool,
    overrides: Dict[Callable[..., Any], Callable[..., Any]],
    exception_registry: ExceptionRegistry,
    error_log: Optional[Callable[[str, Exception], None]] = None,
) -> Callable[..., Any]:
    mapped_ctx = get_mapped_ctx(
        func=func,
        context={req_t: None, AsyncContext: None},
        allow_incomplete=False,
        validate=True,
        overrides=overrides,
    )

    async def method(self: Any, request: Any, context: AsyncContext) -> Any:
        try:
            ctx = {req_t: request, AsyncContext: context}
            kwargs = await resolve_mapped_ctx(ctx, mapped_ctx)
            response = await func(**kwargs)
            return response
        except Exception as e:
            if error_log is not None:
                error_log(func.__name__, e)
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
            ctx = {req_t: request, AsyncContext: context}
            kwargs = await resolve_mapped_ctx(ctx, mapped_ctx)
            async for resp in func(**kwargs):
                yield resp
        except Exception as e:
            if error_log is not None:
                error_log(func.__name__, e)
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


def make_service_class(
    service: IService,
    module: IServiceModule,
    methods: Dict[str, Callable[..., Any]],
) -> Type[Any]:
    baseclass = module.get_service_baseclass(service.name)
    service_class = provide_service_class(
        service.name, baseclass, methods, (service.package, service.module)
    )
    return service_class


class classproperty:
    def __init__(self, fget):
        self.fget = classmethod(fget)

    def __get__(self, obj, owner):
        return self.fget.__get__(obj, owner)()


def provide_service_class(
    name: str,
    baseclass: type,
    methods: dict[str, Callable[..., Any]],
    label: Tuple[str, str],
) -> Type[Any]:

    @classproperty
    def _label(_: Any) -> Tuple[str, str]:
        return label

    methods["label"] = _label
    return type(name, (baseclass,), methods)

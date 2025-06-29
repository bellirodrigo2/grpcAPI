from functools import partial
from types import ModuleType
from typing import Any, AsyncGenerator, Callable, Dict, List, Optional, Tuple, Type

from grpcAPI.app import App
from grpcAPI.ctxinject.inject import get_mapped_ctx, resolve_mapped_ctx
from grpcAPI.exceptionhandler import ExceptionRegistry
from grpcAPI.proto_inject import extract_models, proto_inject_validation
from grpcAPI.proto_proxy import bind_proto_proxy
from grpcAPI.proxy import IteratorProxy
from grpcAPI.types import Context, IPackage, IService, Stream, get_func_arg_info


def load_services(
    app: App, modules: Dict[str, Dict[str, ModuleType]]
) -> List[Type[Any]]:
    inject_validation_wrapper = partial(
        proto_inject_validation, argproc=app.casting_dict
    )

    transform_func = inject_validation_wrapper
    overrides = app.dependency_overrides
    exception_registry = app._exception_handlers
    return make_service_classes(
        app.packages,
        modules,
        transform_func,
        overrides,
        exception_registry,
        app.error_log,
    )


def make_service_classes(
    packs: List[IPackage],
    modules: Dict[str, Dict[str, ModuleType]],
    transform_func: Callable[[Callable[..., Any]], Callable[..., Any]],
    overrides: Dict[Callable[..., Any], Callable[..., Any]],
    exception_registry: ExceptionRegistry,
    error_log: Optional[Callable[[str, Exception], None]] = None,
) -> List[type[Any]]:

    service_clss: List[type[Any]] = []
    for pack in packs:
        for module in pack.modules:
            for service in module.services:
                service_cls = make_service_class(
                    service,
                    modules,
                    transform_func,
                    overrides,
                    exception_registry,
                    error_log,
                )
                service_clss.append(service_cls)
    return service_clss


def get_baseclass(
    service: IService,
    modules: Dict[str, Dict[str, ModuleType]],
    methods: Dict[str, Callable[..., Any]],
) -> Type[Any]:
    module_str = f"{service.module}_grpc"
    service_grpc = modules[service.package][module_str]
    baseclass = getattr(service_grpc, f"{service.name}Servicer")
    service_class = provide_service_class(
        service.name, baseclass, methods, (service.package, service.module)
    )
    return service_class


def make_service_class(
    service: IService,
    modules: Dict[str, Dict[str, ModuleType]],
    transform_func: Callable[[Callable[..., Any]], Callable[..., Any]],
    overrides: Dict[Callable[..., Any], Callable[..., Any]],
    exception_registry: ExceptionRegistry,
    error_log: Optional[Callable[[str, Exception], None]] = None,
) -> Type[Any]:

    methods: Dict[str, Callable[..., Any]] = {}
    for method in service.methods:

        request_type, response_type = extract_models(method.method)

        request_model, request_stream = get_func_arg_info(request_type)
        response_model, response_stream = get_func_arg_info(response_type)

        bind_proto_proxy(request_model, modules[str(request_model.package())])
        bind_proto_proxy(response_model, modules[str(response_model.package())])
        service_method = make_method(
            method.method,
            request_model,
            request_stream,
            response_stream,
            transform_func,
            overrides,
            exception_registry,
            error_log,
        )
        methods[method.method.__name__] = service_method

    service_class = get_baseclass(service, modules, methods)
    return service_class


def make_method(
    func: Callable[..., Any],
    request_type: Type[Any],
    request_stream: bool,
    response_stream: bool,
    transform_func: Callable[[Callable[..., Any]], Callable[..., Any]],
    overrides: Dict[Callable[..., Any], Callable[..., Any]],
    exception_registry: ExceptionRegistry,
    error_log: Optional[Callable[[str, Exception], None]] = None,
) -> Callable[..., Any]:

    func = transform_func(func)

    getctx = get_stream_ctx if request_stream else get_ctx

    req_t = Stream[request_type] if request_stream else request_type
    mapped_ctx = get_mapped_ctx(
        func,
        context={req_t: None, Context: None},
        allow_incomplete=False,
        validate=True,
        transform_func=transform_func,
        overrides=overrides,
    )

    async def method(self: Any, request: Any, context: Context) -> Any:
        try:
            ctx = getctx(request_type, request, context)
            return await resolve_method(func, ctx, mapped_ctx)
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

    async def stream_method(
        self: Any, request: Any, context: Context
    ) -> AsyncGenerator[Any, Any]:
        try:
            ctx = getctx(request_type, request, context)
            async for resp in resolve_stream_method(func, ctx, mapped_ctx):
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
                print(f"Error on method '{func.__name__}': \n \t{str(e)}")
                raise e

    return stream_method if response_stream else method


def get_ctx(req_type: Type[Any], request: Any, context: Any) -> Dict[Any, Any]:
    proxyreq = req_type(request)
    return {req_type: proxyreq, Context: context}


def get_stream_ctx(req_type: Type[Any], request: Any, context: Any) -> Dict[Any, Any]:
    req_iter = IteratorProxy(request, req_type)
    return {Stream[req_type]: req_iter, Context: context}


async def resolve_method(
    func: Callable[..., Any], ctx: Dict[Any, Any], mapped_ctx: Dict[Any, Any]
) -> Any:
    kwargs = await resolve_mapped_ctx(ctx, mapped_ctx)
    proxy_response = await func(**kwargs)
    return proxy_response.unwrap


async def resolve_stream_method(
    func: Callable[..., Any], ctx: Dict[Any, Any], mapped_ctx: Dict[Any, Any]
) -> AsyncGenerator[Any, Any]:
    kwargs = await resolve_mapped_ctx(ctx, mapped_ctx)
    async for resp in func(**kwargs):
        yield resp.unwrap


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


# async def method(self, request, context: Context):
#     try:
#         async def call_final():
#             ctx = getctx(request_type, request, context)
#             return await resolve_method(func, ctx, mapped_ctx)

#         return await wrap_with_middlewares(
#             middlewares,
#             call_final,
#             request,
#             context
#         )

#     except Exception as e:
#         exc_handler = exception_registry.get(type(e), None)
#         if exc_handler is not None:
#             err_code, err_msg = exc_handler(e)
#             context.abort(err_code.value, err_msg)


# async def stream_method(self, request, context: Context):
#     try:
#         async def call_final():
#             ctx = getctx(request_type, request, context)
#             async for resp in resolve_stream_method(func, ctx, mapped_ctx):
#                 yield resp

#         async for item in wrap_stream_with_middlewares(
#             middlewares,
#             call_final,
#             request,
#             context
#         ):
#             yield item

#     except Exception as e:
#         exc_handler = exception_registry.get(type(e), None)
#         if exc_handler is not None:
#             err_code, err_msg = exc_handler(e)
#             context.abort(err_code.value, err_msg)

import inspect
from collections.abc import Callable
from contextlib import AsyncExitStack
from typing import Type

from typing_extensions import Any, Dict

from grpcAPI import ExceptionRegistry
from grpcAPI.data_types import AsyncContext, get_function_metadata
from grpcAPI.makeproto import ILabeledMethod
from grpcAPI.proto_ctxinject import get_mapped_ctx, resolve_mapped_ctx


async def safe_run(
    func: Callable[..., Any], *args: Any, **kwargs: Any
) -> None:  # pragma: no cover
    result = func(*args, **kwargs)
    if inspect.isawaitable(result):
        await result


def make_method_async(
    labeledmethod: ILabeledMethod,
    overrides: Dict[Callable[..., Any], Callable[..., Any]],
    exception_registry: ExceptionRegistry,
) -> Callable[..., Any]:
    """Async implementarion for MakeMethod using ctxinject"""

    try:
        req_t = labeledmethod.input_type
        func = labeledmethod.method
        factory = (
            make_stream_runner if labeledmethod.is_server_stream else make_unary_runner
        )

    except (AttributeError, IndexError) as e:
        raise type(e)(
            f"Not able to make method for: {labeledmethod.name}:\n Error:{str(e)}"
        )

    return factory(
        func=func,
        overrides=overrides,
        exception_registry=exception_registry,
        req=req_t,
    )


class CtxMngr:
    def __init__(self, req: Type[Any], func: Callable[..., Any]) -> None:
        self.req = req
        self.bynames = get_function_metadata(func)

    def get_ctx_template(self) -> Dict[Any, Any]:
        if self.bynames is None:
            return {self.req: None, AsyncContext: None}
        return {**self.bynames, AsyncContext: None}

    def get_ctx(self, req: Any, context: AsyncContext) -> Dict[Any, Any]:
        if self.bynames is None:
            return {self.req: req, AsyncContext: context}
        ctx = {k: getattr(req, k) for k in self.bynames.keys()}
        return {**ctx, AsyncContext: context}


class Runner:
    __slots__ = (
        "func",
        "exception_registry",
        "mapped_ctx",
        "resolve_func",
        "req",
        "ctx_mngr",
        "overrides",
    )

    def __init__(
        self,
        func: Callable[..., Any],
        overrides: Dict[Callable[..., Any], Callable[..., Any]],
        exception_registry: ExceptionRegistry,
        req: Type[Any],
        order: bool = True,
    ):
        self.func = func
        self.overrides = overrides
        self.exception_registry = exception_registry
        self.req = req
        self.ctx_mngr = CtxMngr(req, func)

        context = self.ctx_mngr.get_ctx_template()
        self.mapped_ctx = get_mapped_ctx(
            func=func,
            context=context,
            allow_incomplete=False,
            validate=True,
            overrides=overrides,
            ordered=order,
        )

    async def _make_kwargs(
        self, request: Any, context: AsyncContext, stack: AsyncExitStack
    ) -> Any:
        ctx = self.ctx_mngr.get_ctx(request, context)
        return await resolve_mapped_ctx(ctx, self.mapped_ctx, stack)

    async def _handle_exception(self, e: Exception, context: AsyncContext) -> None:
        exc_handler = self.exception_registry.get(type(e), None)
        if exc_handler is not None:
            await safe_run(exc_handler, e, context)
        else:
            raise e


def make_unary_runner(
    func: Callable[..., Any],
    overrides: Dict[Callable[..., Any], Callable[..., Any]],
    exception_registry: ExceptionRegistry,
    req: Type[Any],
) -> Callable[[Any, AsyncContext], Any]:
    """Factory function to create a unary RPC handler function"""

    runner = Runner(func, overrides, exception_registry, req)

    async def unary_handler(request: Any, context: AsyncContext) -> Any:
        try:
            async with AsyncExitStack() as stack:
                kwargs = await runner._make_kwargs(request, context, stack)
                response = await runner.func(**kwargs)
                return response
        except Exception as e:
            await runner._handle_exception(e, context)

    return unary_handler


def make_stream_runner(
    func: Callable[..., Any],
    overrides: Dict[Callable[..., Any], Callable[..., Any]],
    exception_registry: ExceptionRegistry,
    req: Type[Any],
) -> Callable[[Any, AsyncContext], Any]:
    """Factory function to create a streaming RPC handler function"""

    runner = Runner(func, overrides, exception_registry, req)

    async def stream_handler(request: Any, context: AsyncContext) -> Any:
        try:
            async with AsyncExitStack() as stack:
                kwargs = await runner._make_kwargs(request, context, stack)
                async for resp in runner.func(**kwargs):
                    yield resp
        except Exception as e:
            await runner._handle_exception(e, context)

    return stream_handler

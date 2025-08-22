import inspect
from collections.abc import Callable
from contextlib import AsyncExitStack
from typing import Type

from typing_extensions import Any, Dict

from grpcAPI import ExceptionRegistry
from grpcAPI.data_types import AsyncContext, get_function_metadata
from grpcAPI.makeproto import ILabeledMethod
from grpcAPI.proto_ctxinject import (
    get_mapped_ctx,
    get_mapped_ctx_ordered,
    resolve_mapped_ctx,
    resolve_mapped_ctx_ordered,
)


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
        cls_factory = StreamRunner if labeledmethod.is_server_stream else UnaryRunner

    except (AttributeError, IndexError) as e:
        raise type(e)(
            f"Not able to make method for: {labeledmethod.name}:\n Error:{str(e)}"
        )
    runner = cls_factory(
        func=func,
        overrides=overrides,
        exception_registry=exception_registry,
        req=req_t,
    )
    return runner


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
        order: bool = False,
    ):
        self.func = func
        self.overrides = overrides
        self.exception_registry = exception_registry
        self.req = req
        self.ctx_mngr = CtxMngr(req, func)

        if order:
            get_mapped = get_mapped_ctx_ordered
            self.resolve_func = resolve_mapped_ctx_ordered
        else:
            get_mapped = get_mapped_ctx
            self.resolve_func = resolve_mapped_ctx

        context = self.ctx_mngr.get_ctx_template()
        self.mapped_ctx = get_mapped(
            func=func,
            context=context,
            allow_incomplete=False,
            validate=True,
            overrides=overrides,
        )

    async def _make_kwargs(
        self, request: Any, context: AsyncContext, stack: AsyncExitStack
    ) -> Any:
        ctx = self.ctx_mngr.get_ctx(request, context)
        return await self.resolve_func(ctx, self.mapped_ctx, stack)

    async def _handle_exception(self, e: Exception, context: AsyncContext) -> None:
        exc_handler = self.exception_registry.get(type(e), None)
        if exc_handler is not None:
            await safe_run(exc_handler, e, context)
        else:
            raise e


class UnaryRunner(Runner):

    async def __call__(self, request: Any, context: AsyncContext) -> Any:
        try:
            async with AsyncExitStack() as stack:
                kwargs = await self._make_kwargs(request, context, stack)
                response = await self.func(**kwargs)
                return response
        except Exception as e:
            await self._handle_exception(e, context)


class StreamRunner(Runner):

    async def __call__(self, request: Any, context: AsyncContext) -> Any:
        try:
            async with AsyncExitStack() as stack:
                kwargs = await self._make_kwargs(request, context, stack)
                async for resp in self.func(**kwargs):
                    yield resp
        except Exception as e:
            await self._handle_exception(e, context)

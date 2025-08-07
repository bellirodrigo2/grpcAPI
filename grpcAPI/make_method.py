import inspect
from collections.abc import AsyncIterator, Callable
from contextlib import AsyncExitStack

from typing_extensions import Any, Dict

from grpcAPI import ExceptionRegistry
from grpcAPI.data_types import AsyncContext
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
        req_t = labeledmethod.request_types[0]
        func = labeledmethod.method
        is_stream = labeledmethod.response_types.origin is AsyncIterator
    except (AttributeError, IndexError) as e:
        raise type(e)(
            f"Not able to make method for: {labeledmethod.name}:\n Error:{str(e)}"
        )
    mapped_ctx = get_mapped_ctx(
        func=func,
        context={req_t.argtype: None, AsyncContext: None},
        allow_incomplete=False,
        validate=True,
        overrides=overrides,
    )

    async def method(request: Any, context: AsyncContext) -> Any:
        try:
            async with AsyncExitStack() as stack:
                ctx = {req_t.argtype: request, AsyncContext: context}
                kwargs = await resolve_mapped_ctx(ctx, mapped_ctx, stack=stack)
                response = await func(**kwargs)
                return response
        except Exception as e:
            exc_handler = exception_registry.get(type(e), None)
            if exc_handler is not None:
                await safe_run(exc_handler, e, context)
            else:
                raise e

    async def stream_method(request: Any, context: AsyncContext) -> Any:
        try:
            async with AsyncExitStack() as stack:
                ctx = {req_t.argtype: request, AsyncContext: context}
                kwargs = await resolve_mapped_ctx(ctx, mapped_ctx, stack)
                async for resp in func(**kwargs):
                    yield resp
        except Exception as e:
            exc_handler = exception_registry.get(type(e), None)
            if exc_handler is not None:
                await safe_run(exc_handler, e, context)
            else:
                raise e

    return stream_method if is_stream else method

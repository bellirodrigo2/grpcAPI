from collections.abc import AsyncIterator, Callable

from ctxinject.inject import get_mapped_ctx, resolve_mapped_ctx
from makeproto import ILabeledMethod
from typing_extensions import Any, Dict

from grpcAPI import ExceptionRegistry
from grpcAPI.types import AsyncContext


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

    async def method(request: Any, context: AsyncContext) -> Any:
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

    async def stream_method(request: Any, context: AsyncContext) -> Any:
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

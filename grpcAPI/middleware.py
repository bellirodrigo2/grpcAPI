from typing import Any, Awaitable, Callable

from grpcAPI.context import Context

type Middleware = Callable[[Any, Context, Callable[[], Awaitable[Any]]], Awaitable[Any]]


def wrap_with_middlewares(
    middlewares: list[Middleware],
    call_final: Callable[[], Awaitable[Any]],
    request: Any,
    context: Context,
) -> Awaitable[Any]:
    handler = call_final
    for middleware in reversed(middlewares):
        current_handler = handler
        handler = lambda req=request, ctx=context, next_call=current_handler, mw=middleware: mw(
            req, ctx, next_call
        )
    return handler()

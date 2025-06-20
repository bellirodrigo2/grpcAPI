from types import CoroutineType
from typing import Any, AsyncGenerator, Callable, Dict, Literal

from grpcAPI.ctxinject.inject import get_mapped_ctx, inject_args, resolve_mapped_ctx
from grpcAPI.proxy import IteratorProxy
from grpcAPI.types import IService
from grpcAPI.types.context import Context
from grpcAPI.types.method import Stream


def make_service_class(service: IService, modules: Dict[Any, Any]) -> type[Any]:
    pass


def make_method(
    request_type: type[Any],
    func: Callable[..., Any],
    method_type: Literal["unary", "client_stream", "server_stream", "bilateral"],
) -> Callable[..., Any]:
    pass


async def make_unary(request_type: type[Any], method: Callable[..., Any]):
    mapped_ctx = await get_mapped_ctx(
        method, context={request_type: None, Context: None}
    )

    async def unary(self, request, context):
        proxyreq = request_type(request)
        ctx = {request_type: proxyreq, Context: context}
        kwargs = await resolve_mapped_ctx(ctx, mapped_ctx)
        proxy_response = await method(**kwargs)
        return proxy_response.unwrap

    return unary


def make_client_stream(
    request_type: type[Any], method: Callable[..., Any], mapped_ctx: Dict[Any, Any]
):
    async def client_stream(self, request_iterator, context):
        req_iter = IteratorProxy(request_iterator, request_type)
        ctx = {Stream[request_type]: req_iter, Context: context}
        kwargs = await resolve_mapped_ctx(ctx, mapped_ctx)
        proxy_response = await method(**kwargs)
        return proxy_response.unwrap

    return client_stream


def make_server_stream(
    request_type: type[Any], method: Callable[..., Any], mapped_ctx: Dict[Any, Any]
):
    async def server_stream(self, request, context):
        proxyreq = request_type(request)
        ctx = {request_type: proxyreq, Context: context}
        kwargs = await resolve_mapped_ctx(ctx, mapped_ctx)
        async for resp in method(**kwargs):
            yield resp.unwrap

    return server_stream


def make_bilateral(
    request_type: type[Any], method: Callable[..., Any], mapped_ctx: Dict[Any, Any]
):
    async def bilateral(self, request_iterator, context):
        req_iter = IteratorProxy(request_iterator, request_type)
        ctx = {Stream[request_type]: req_iter, Context: context}
        kwargs = await resolve_mapped_ctx(ctx, mapped_ctx)
        async for resp in method(**kwargs):
            yield resp.unwrap

    return bilateral

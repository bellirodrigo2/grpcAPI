from typing import Any, Callable, Dict

from grpcAPI.ctxinject.inject import get_mapped_ctx, resolve_mapped_ctx
from grpcAPI.proxy import IteratorProxy
from grpcAPI.types import IService
from grpcAPI.types.context import Context
from grpcAPI.types.method import Stream


def make_service_class(service: IService, modules: Dict[Any, Any]) -> type[Any]:
    # dado o service
    # descobrir se é unary, client_stream, server_stream ou bilateral
    # descobrir qual o request model
    # extract_request from proto_inject
    pass


async def make_method(
    request_type: type[Any],
    func: Callable[..., Any],
    request_stream: bool,
    response_stream: bool,
) -> Callable[..., Any]:

    getctx = get_stream_ctx if request_stream else get_ctx

    req_t = Stream[request_type] if request_stream else request_type
    mapped_ctx = await get_mapped_ctx(func, {req_t: None, Context: None})

    async def method(self, request, context):
        ctx = getctx(request_type, request, context)
        return await resolve_method(func, ctx, mapped_ctx)

    async def stream_method(self, request, context):
        ctx = getctx(request_type, request, context)
        async for resp in resolve_stream_method(func, ctx, mapped_ctx):
            yield resp

    return stream_method if response_stream else method


def get_ctx(req_type: type[Any], request: Any, context: Any) -> Dict[Any, Any]:
    proxyreq = req_type(request)
    return {req_type: proxyreq, Context: context}


def get_stream_ctx(req_type: type[Any], request: Any, context: Any) -> Dict[Any, Any]:
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
):
    kwargs = await resolve_mapped_ctx(ctx, mapped_ctx)
    async for resp in func(**kwargs):
        yield resp.unwrap

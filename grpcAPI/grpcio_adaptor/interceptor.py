from grpc import aio
from typing_extensions import Any, AsyncIterator, Awaitable, Callable, TypeVar

from grpcAPI.context import AsyncContext

# Type variables for request and response message types
Req = TypeVar("Req")
Res = TypeVar("Res")


class BaseAioInterceptor(aio.ServerInterceptor[Req, Res]):
    """
    Base interceptor for grpc.aio that dispatches to one of four methods,
    depending on the RPC call pattern:
      - intercept_unary:           unary-unary calls
      - intercept_client_stream:   stream-unary calls
      - intercept_server_stream:   unary-stream calls
      - intercept_bilateral_stream: stream-stream calls

    Subclasses may override any of these four methods.
    """

    async def intercept_service(self, continuation, handler_call_details):
        # Retrieve the next handler in the chain
        handler = await continuation(handler_call_details)
        if handler is None:
            return None

        # Wrap each possible RPC handler type
        if handler.unary_unary:
            return aio.unary_unary_rpc_method_handler(
                self._wrap_unary_unary(handler.unary_unary, handler_call_details),
                request_deserializer=handler.request_deserializer,
                response_serializer=handler.response_serializer,
            )

        if handler.unary_stream:
            return aio.unary_stream_rpc_method_handler(
                self._wrap_unary_stream(handler.unary_stream, handler_call_details),
                request_deserializer=handler.request_deserializer,
                response_serializer=handler.response_serializer,
            )

        if handler.stream_unary:
            return aio.stream_unary_rpc_method_handler(
                self._wrap_stream_unary(handler.stream_unary, handler_call_details),
                request_deserializer=handler.request_deserializer,
                response_serializer=handler.response_serializer,
            )

        if handler.stream_stream:
            return aio.stream_stream_rpc_method_handler(
                self._wrap_stream_stream(handler.stream_stream, handler_call_details),
                request_deserializer=handler.request_deserializer,
                response_serializer=handler.response_serializer,
            )

        # Fallback: return the unmodified handler
        return handler

    def _wrap_unary_unary(
        self,
        handler_fn,
        details,
    ):
        async def wrapper(request, context) -> Res:
            return await self.intercept_unary(handler_fn, request, context, details)

        return wrapper

    def _wrap_unary_stream(
        self,
        handler_fn,
        details,
    ):
        async def wrapper(request: Req, context):
            async for resp in self.intercept_server_stream(
                handler_fn, request, context, details
            ):
                yield resp

        return wrapper

    def _wrap_stream_unary(
        self,
        handler_fn,
        details,
    ):
        async def wrapper(request_iter, context) -> Res:
            return await self.intercept_client_stream(
                handler_fn, request_iter, context, details
            )

        return wrapper

    def _wrap_stream_stream(
        self,
        handler_fn,
        details,
    ):
        async def wrapper(request_iter, context):
            async for resp in self.intercept_bilateral_stream(
                handler_fn, request_iter, context, details
            ):
                yield resp

        return wrapper


class AioInterceptor(BaseAioInterceptor[Any, Any]):

    async def intercept_unary(
        self,
        call_next: Callable[[Req, AsyncContext], Awaitable[Res]],
        request: Req,
        context: AsyncContext,
        # details: grpc.HandlerCallDetails,
    ) -> Res:
        """
        Override this to intercept unary-unary RPCs.
        Default: just forwards to the original handler.
        """
        return await call_next(request, context)

    async def intercept_client_stream(
        self,
        call_next: Callable[[AsyncIterator[Req], AsyncContext], Awaitable[Res]],
        request_iterator: AsyncIterator[Req],
        context: AsyncContext,
        # details: grpc.HandlerCallDetails,
    ) -> Res:
        """
        Override this to intercept client-streaming RPCs.
        Default: just forwards to the original handler.
        """
        return await call_next(request_iterator, context)

    async def intercept_server_stream(
        self,
        call_next: Callable[[Req, AsyncContext], AsyncIterator[Res]],
        request: Req,
        context: AsyncContext,
        # details: grpc.HandlerCallDetails,
    ) -> AsyncIterator[Res]:
        """
        Override this to intercept server-streaming RPCs.
        Default: just forwards to the original handler.
        """
        async for response in call_next(request, context):
            yield response

    async def intercept_bilateral_stream(
        self,
        call_next: Callable[[AsyncIterator[Req], AsyncContext], AsyncIterator[Res]],
        request_iterator: AsyncIterator[Req],
        context: AsyncContext,
        # details: grpc.HandlerCallDetails,
    ) -> AsyncIterator[Res]:
        """
        Override this to intercept bidi-streaming RPCs.
        Default: just forwards to the original handler.
        """
        async for response in call_next(request_iterator, context):
            yield response

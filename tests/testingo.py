import asyncio
from collections.abc import AsyncIterator

import grpc
from google.protobuf.wrappers_pb2 import StringValue

from grpcAPI.add_to_server import add_to_server
from grpcAPI.app import APIService
from grpcAPI.server import ServerWrapper
from grpcAPI.types import AsyncContext


async def main() -> None:
    serviceapi = APIService(
        name="functional",
    )

    def _echo(val: StringValue) -> StringValue:
        return StringValue(value=f"echo-{val.value}")

    @serviceapi()
    async def echo(request: StringValue, context: AsyncContext) -> StringValue:
        return _echo(request)

    @serviceapi()
    async def echo_client_stream(
        request_iterator: AsyncIterator[StringValue], context: AsyncContext
    ) -> StringValue:
        final_request = StringValue(value="None")
        async for request in request_iterator:
            final_request = request
        return _echo(final_request)

    @serviceapi()
    async def echo_server_stream(
        request: StringValue, context: AsyncContext
    ) -> AsyncIterator[StringValue]:
        for _ in range(2):
            yield _echo(request)

    @serviceapi()
    async def echo_bilateral(
        request_iterator: AsyncIterator[StringValue], context: AsyncContext
    ) -> AsyncIterator[StringValue]:
        async for request in request_iterator:
            context.peer()
            yield _echo(request)

    _server = grpc.aio.server()
    server = ServerWrapper(_server, ["foo"])
    add_to_server(serviceapi, server, {}, {})

    server.add_insecure_port("0.0.0.0:50051")
    await server.start()
    await server.wait_for_termination()


if __name__ == "__main__":
    asyncio.run(main())

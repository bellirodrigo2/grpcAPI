import asyncio

import grpc
from grpc_reflection.v1alpha import reflection_pb2, reflection_pb2_grpc


async def list_services(host="localhost", port=50051) -> None:
    async with grpc.aio.insecure_channel(f"{host}:{port}") as channel:
        stub = reflection_pb2_grpc.ServerReflectionStub(channel)
        request = reflection_pb2.ServerReflectionRequest(list_services="")
        response_stream = stub.ServerReflectionInfo(iter([request]))

        async for response in response_stream:
            services = response.list_services_response.service
            print("Services available:")
            for service in services:
                print(f" - {service.name}")


if __name__ == "__main__":

    asyncio.run(list_services())

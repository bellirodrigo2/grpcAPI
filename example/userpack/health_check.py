import asyncio

import grpc
from grpc_health.v1 import health_pb2, health_pb2_grpc


async def health_check(host="localhost", port=50051, service_name="") -> None:
    async with grpc.aio.insecure_channel(f"{host}:{port}") as channel:
        stub = health_pb2_grpc.HealthStub(channel)
        request = health_pb2.HealthCheckRequest(service=service_name)
        response = await stub.Check(request)
        status_map = {
            health_pb2.HealthCheckResponse.UNKNOWN: "UNKNOWN",
            health_pb2.HealthCheckResponse.SERVING: "SERVING",
            health_pb2.HealthCheckResponse.NOT_SERVING: "NOT_SERVING",
            health_pb2.HealthCheckResponse.SERVICE_UNKNOWN: "SERVICE_UNKNOWN",
        }
        print(
            f"Health status for '{service_name}': {status_map.get(response.status, 'UNKNOWN')}"
        )


if __name__ == "__main__":

    asyncio.run(health_check(service_name="user_service"))
